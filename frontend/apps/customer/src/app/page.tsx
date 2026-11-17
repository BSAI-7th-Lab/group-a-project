import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function Home() {
  return (
    <main className="grid min-h-screen place-items-center bg-slate-900 px-6 text-white">
      <section className="max-w-xl text-center">
        <div className="mx-auto grid size-16 place-items-center rounded-2xl bg-emerald-400 text-2xl font-black text-slate-950">
          S
        </div>
        <p className="mt-6 text-sm font-semibold uppercase tracking-[0.2em] text-emerald-300">
          The restaurant, in sync
        </p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight sm:text-5xl">
          Welcome to SwarmDining
        </h1>
        <p className="mx-auto mt-5 max-w-md text-lg leading-8 text-slate-300">
          Scan your table&apos;s QR code to explore the menu and order when
          you&apos;re ready.
        </p>
        <Button className="mt-8" render={<Link href="/t/4" />}>
          Preview table 4
        </Button>
      </section>
    </main>
  );
}
