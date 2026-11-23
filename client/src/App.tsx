import { useTranslation } from 'react-i18next';

// TODO(piyush): replace with the router and screens from plan section 8.
export default function App() {
  const { t } = useTranslation();
  return (
    <main className="mx-auto max-w-md p-4">
      <h1 className="text-2xl font-bold text-brand">{t('app.name')}</h1>
      <p className="mt-2">{t('app.tagline')}</p>
    </main>
  );
}
