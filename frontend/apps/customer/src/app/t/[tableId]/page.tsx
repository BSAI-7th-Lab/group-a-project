type TablePageProps = {
  params: Promise<{ tableId: string }>;
};

export const instant = false;

export default async function TablePage({ params }: TablePageProps) {
  const { tableId } = await params;

  return (
    <main className="grid min-h-screen place-items-center bg-slate-900 px-6 text-white">
      <div className="text-center">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-300">
          SwarmDining
        </p>
        <h1 className="mt-4 text-3xl font-bold">Welcome to your table</h1>
        <p className="mt-2 text-slate-300">Table {tableId}</p>
      </div>
    </main>
  );
}
