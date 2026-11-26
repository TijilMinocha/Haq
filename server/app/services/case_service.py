from datetime import UTC, date, datetime

from app.core.attempts import AttemptStore
from app.core.clock import today_ist
from app.core.errors import AppError, invalid_credentials, invalid_dates
from app.core.security import (
    DECOY_SECRET_HASH,
    hash_case_token,
    hash_secret,
    new_case_code,
    new_case_token,
    new_id,
    verify_secret,
)
from app.domain.models import CaseMode, Language
from app.infra.db.repositories import CaseRecord, CaseRepository
from app.schemas.case import (
    CaseCreate,
    CaseCreated,
    CaseResume,
    CaseResumed,
    CaseSummary,
    CaseUpdate,
    CaseView,
    Event,
    Nominee,
    Subject,
)
from app.schemas.document import DocumentView
from app.schemas.evaluation import Evaluation
from app.services.evaluation_service import evaluate
from app.services.stub_scenarios import load_scenario

DEMO_PIN = "1234"
# One household shares an IP and may mistype its own PIN; a bot walking through case codes
# has no such excuse, so the per-IP budget for failed resumes is several times the per-code one.
IP_ATTEMPT_FACTOR = 4


def _reject_impossible_dates(view: CaseView, today: date) -> None:
    date_of_birth = view.subject.date_of_birth
    event_date = view.event.date
    if event_date is not None and event_date > today:
        raise invalid_dates("event.date", "in_future")
    if date_of_birth is not None and date_of_birth > today:
        raise invalid_dates("subject.date_of_birth", "in_future")
    if date_of_birth is not None and event_date is not None and date_of_birth > event_date:
        raise invalid_dates("subject.date_of_birth", "birth_after_event")


class CaseService:
    def __init__(
        self, cases: CaseRepository, attempts: AttemptStore, ip_attempts: AttemptStore
    ) -> None:
        self._cases = cases
        self._attempts = attempts
        self._ip_attempts = ip_attempts

    async def create(self, data: CaseCreate, operator_id: str | None) -> CaseCreated:
        view = CaseView(
            id=new_id("c"),
            code=await self._unique_code(),
            mode=data.mode,
            language=data.language,
            subject=Subject(),
            event=Event(),
            nominee=Nominee(),
            documents=[],
            evaluation=Evaluation(),
            updated_at=datetime.now(UTC),
        )
        return await self._store(view, data.pin, operator_id, scenario_id=None)

    async def start_demo(self, scenario_id: str, operator_id: str | None) -> CaseCreated:
        fixture = load_scenario(scenario_id)
        if fixture is None:
            raise AppError("scenario_not_found", 404, "Unknown demo scenario.")
        view = CaseView(
            id=new_id("c"),
            code=await self._unique_code(),
            mode=CaseMode(fixture["mode"]),
            language=Language(fixture["language"]),
            subject=Subject.model_validate(fixture["subject"]),
            event=Event.model_validate(fixture["event"]),
            nominee=Nominee.model_validate(fixture["nominee"]),
            documents=[DocumentView.model_validate(d) for d in fixture["documents"]],
            evaluation=Evaluation(),
            updated_at=datetime.now(UTC),
        )
        return await self._store(view, DEMO_PIN, operator_id, scenario_id=scenario_id)

    async def resume(self, data: CaseResume, client: str) -> CaseResumed:
        guards = self._resume_guards(data.case_code, client)
        for store, key in guards:
            await store.check(key)
        record = await self._cases.get_by_code(data.case_code)
        # A code that does not exist still pays for a hash, so response time cannot be
        # used to find out which codes are real.
        stored = record.pin_hash if record is not None else DECOY_SECRET_HASH
        valid = verify_secret(stored, data.pin)
        if record is None or not valid:
            for store, key in guards:
                await store.fail(key)
            raise invalid_credentials()
        for store, key in guards:
            await store.reset(key)
        token = new_case_token()
        record.token_hashes.add(hash_case_token(token))
        await self._cases.save(record)
        return CaseResumed(case_id=record.view.id, access_token=token)

    def _resume_guards(self, code: str, client: str) -> tuple[tuple[AttemptStore, str], ...]:
        # Counted separately, so guesses spread over many codes still add up per caller.
        return ((self._attempts, f"case:{code}"), (self._ip_attempts, f"ip:{client}"))

    def view(self, record: CaseRecord) -> CaseView:
        return record.view.model_copy(update={"evaluation": evaluate(record.view)})

    async def update(self, record: CaseRecord, patch: CaseUpdate) -> CaseView:
        changes = patch.model_dump(exclude_unset=True)
        merged = {
            key: getattr(record.view, key).model_copy(update=value)
            if isinstance(value, dict)
            else value
            for key, value in changes.items()
        }
        updated = record.view.model_copy(update={**merged, "updated_at": datetime.now(UTC)})
        # The patch may carry only the event date, so compare it with the saved date of birth.
        _reject_impossible_dates(updated, today_ist())
        record.view = updated
        await self._cases.save(record)
        return self.view(record)

    async def list_for_operator(
        self, operator_id: str, status: str | None, q: str | None
    ) -> list[CaseSummary]:
        summaries = [self._summary(r) for r in await self._cases.list_by_owner(operator_id)]
        if status:
            summaries = [s for s in summaries if s.status == status]
        if q:
            needle = q.strip().lower()
            summaries = [
                s
                for s in summaries
                if needle in s.code.lower() or needle in (s.subject_name or "").lower()
            ]
        return sorted(summaries, key=lambda s: s.updated_at, reverse=True)

    def _summary(self, record: CaseRecord) -> CaseSummary:
        view = self.view(record)
        blockers = sum(1 for f in view.evaluation.flags if f.severity == "blocker")
        if not view.documents:
            status = "new"
        elif blockers:
            status = "blocked"
        else:
            status = "ready"
        return CaseSummary(
            id=view.id,
            code=view.code,
            mode=view.mode,
            subject_name=view.subject.name,
            total_claimable=view.evaluation.total_claimable,
            blocker_count=blockers,
            status=status,
            updated_at=view.updated_at,
        )

    async def _store(
        self, view: CaseView, pin: str, operator_id: str | None, scenario_id: str | None
    ) -> CaseCreated:
        token = new_case_token()
        await self._cases.add(
            CaseRecord(
                view=view,
                pin_hash=hash_secret(pin),
                token_hashes={hash_case_token(token)},
                owner_operator_id=operator_id,
                scenario_id=scenario_id,
            )
        )
        return CaseCreated(case_id=view.id, case_code=view.code, access_token=token)

    async def _unique_code(self) -> str:
        while True:
            code = new_case_code()
            if await self._cases.get_by_code(code) is None:
                return code
