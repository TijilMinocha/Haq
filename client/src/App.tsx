import { BrowserRouter, Navigate, Route, Routes } from 'react-router';
import { AppShell } from '@/components/layout/AppShell';
import { LandingScreen } from '@/features/landing/LandingScreen';
import { CaseCreatedScreen } from '@/features/cases/CaseCreatedScreen';
import { ResumeScreen } from '@/features/cases/ResumeScreen';
import { EventScreen } from '@/features/event/EventScreen';
import { ScanScreen } from '@/features/scan/ScanScreen';
import { ResultScreen } from '@/features/result/ResultScreen';
import { DocumentsScreen } from '@/features/documents/DocumentsScreen';
import { SubmitScreen } from '@/features/submit/SubmitScreen';
import { AlertsScreen } from '@/features/alerts/AlertsScreen';
import { OperatorLoginScreen } from '@/features/operator/OperatorLoginScreen';
import { OperatorCasesScreen } from '@/features/operator/OperatorCasesScreen';
import { DemoScreen } from '@/features/demo/DemoScreen';

export default function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<LandingScreen />} />
          <Route path="/resume" element={<ResumeScreen />} />
          <Route path="/case/:id/created" element={<CaseCreatedScreen />} />
          <Route path="/case/:id/event" element={<EventScreen />} />
          <Route path="/case/:id/scan" element={<ScanScreen />} />
          <Route path="/case/:id/result" element={<ResultScreen />} />
          <Route path="/case/:id/documents" element={<DocumentsScreen />} />
          <Route path="/case/:id/submit" element={<SubmitScreen />} />
          <Route path="/case/:id/alerts" element={<AlertsScreen />} />
          <Route path="/operator/login" element={<OperatorLoginScreen />} />
          <Route path="/operator" element={<OperatorCasesScreen />} />
          <Route path="/demo" element={<DemoScreen />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
}
