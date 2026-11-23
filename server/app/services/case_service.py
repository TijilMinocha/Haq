from datetime import UTC, datetime

from app.core.attempts import AttemptLimiter
from app.core.errors import AppError, invalid_credentials
from app.core.security import (
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


class CaseService:
    def __init__(self, cases: CaseRepository, limiter: AttemptLimiter) -> None:
        self._cases = cases
        self._limiter = limiter

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

    async def resume(self, data: CaseResume) -> CaseResumed:
        self._limiter.check(data.case_code)
        record = await self._cases.get_by_code(data.case_code)
        if record is None or not verify_secret(record.pin_hash, data.pin):
            self._limiter.fail(data.case_code)
            raise invalid_credentials()
        self._limiter.reset(data.case_code)
        token = new_case_token()
        record.token_hashes.add(hash_case_token(token))
        await self._cases.save(record)
        return CaseResumed(case_id=record.view.id, access_token=token)

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
        record.view = record.view.model_copy(update={**merged, "updated_at": datetime.now(UTC)})
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
