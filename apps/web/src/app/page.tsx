import {
  Activity,
  ArrowRight,
  Blocks,
  BrainCircuit,
  ChartNoAxesCombined,
  Check,
  Database,
  Globe2,
  Layers3,
  LockKeyhole,
  Network,
  ShieldCheck,
  Sparkles,
  Waypoints,
} from "lucide-react";
import Link from "next/link";
import { Button } from "@atlas/ui/button";
import { Card } from "@atlas/ui/card";
import { ThemeToggle } from "@/components/theme-toggle";

const features = [
  {
    icon: Layers3,
    title: "One financial workspace",
    description: "Bring portfolios, markets, research, and decisions into one coherent system.",
  },
  {
    icon: BrainCircuit,
    title: "Intelligence with context",
    description: "Understand what matters, why it matters, and how it connects to your goals.",
  },
  {
    icon: ShieldCheck,
    title: "Risk built in",
    description: "Institutional-grade controls and transparent reasoning at every layer.",
  },
  {
    icon: Globe2,
    title: "Access without borders",
    description: "A global platform designed to make investing accessible from just $10.",
  },
];

const roadmap = [
  {
    phase: "Foundation",
    status: "Now",
    text: "Secure platform, core infrastructure, and unified design system.",
  },
  {
    phase: "Intelligence",
    status: "Next",
    text: "Market context, portfolio insights, and explainable decision support.",
  },
  {
    phase: "Expansion",
    status: "Future",
    text: "Multi-asset access, automation, and a global investment network.",
  },
];

export default function HomePage() {
  return (
    <main className="min-h-screen overflow-hidden">
      <header className="border-border/60 bg-background/80 fixed inset-x-0 top-0 z-50 border-b backdrop-blur-xl">
        <nav
          className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-8"
          aria-label="Primary navigation"
        >
          <Link href="/" className="flex items-center gap-2.5" aria-label="Atlas AI home">
            <span className="bg-primary text-primary-foreground grid size-8 place-items-center rounded-lg">
              <Waypoints className="size-4" />
            </span>
            <span className="font-display text-lg font-semibold tracking-tight">Atlas AI</span>
          </Link>
          <div className="text-muted-foreground hidden items-center gap-8 text-sm md:flex">
            <a className="hover:text-foreground transition-colors" href="#features">
              Platform
            </a>
            <a className="hover:text-foreground transition-colors" href="#architecture">
              Architecture
            </a>
            <a className="hover:text-foreground transition-colors" href="#roadmap">
              Roadmap
            </a>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <Button size="sm" className="hidden sm:inline-flex" asChild>
              <a href="#features">
                Explore Atlas <ArrowRight className="size-4" />
              </a>
            </Button>
          </div>
        </nav>
      </header>

      <section className="relative flex min-h-[92vh] items-center border-b pt-16">
        <div className="atlas-grid absolute inset-0 opacity-70" aria-hidden="true" />
        <div
          className="bg-primary/10 absolute left-1/2 top-20 h-[28rem] w-[50rem] -translate-x-1/2 rounded-full blur-3xl"
          aria-hidden="true"
        />
        <div className="relative mx-auto grid max-w-7xl items-center gap-16 px-6 py-24 lg:grid-cols-[1.08fr_.92fr] lg:px-8">
          <div>
            <div className="bg-card/70 text-muted-foreground mb-7 inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium shadow-sm">
              <Sparkles className="text-primary size-3.5" />
              Investing, reimagined from first principles
            </div>
            <h1 className="font-display max-w-4xl text-balance text-5xl font-semibold leading-[1.03] tracking-[-0.04em] sm:text-6xl lg:text-7xl">
              The Intelligent Investment <span className="text-primary">Operating System.</span>
            </h1>
            <p className="text-muted-foreground mt-7 max-w-2xl text-balance text-lg leading-8">
              Atlas brings your financial world into one clear, connected system—built to help
              anyone invest with confidence, from their first $10 onward.
            </p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Button size="lg" asChild>
                <a href="#features">
                  Explore Atlas <ArrowRight className="size-4" />
                </a>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <a href="#architecture">Explore the platform</a>
              </Button>
            </div>
            <div className="text-muted-foreground mt-9 flex flex-wrap gap-x-6 gap-y-3 text-sm">
              {["Global by design", "Security first", "Built for clarity"].map((item) => (
                <span className="flex items-center gap-2" key={item}>
                  <span className="bg-primary/10 grid size-5 place-items-center rounded-full">
                    <Check className="text-primary size-3" />
                  </span>
                  {item}
                </span>
              ))}
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-lg">
            <div className="from-primary/20 to-accent/15 absolute -inset-8 rounded-[2rem] bg-gradient-to-br via-transparent blur-2xl" />
            <Card className="border-border/80 bg-card/90 shadow-primary/5 relative overflow-hidden p-2 shadow-2xl backdrop-blur">
              <div className="bg-background/80 rounded-[0.6rem] border p-5">
                <div className="mb-8 flex items-center justify-between">
                  <div>
                    <p className="text-muted-foreground text-xs uppercase tracking-[0.18em]">
                      Financial overview
                    </p>
                    <p className="font-display mt-1 text-xl font-semibold">Your world, connected</p>
                  </div>
                  <div className="flex gap-1.5">
                    <span className="bg-primary size-2 rounded-full" />
                    <span className="bg-accent size-2 rounded-full" />
                    <span className="bg-muted-foreground/30 size-2 rounded-full" />
                  </div>
                </div>
                <div className="relative grid h-64 place-items-center">
                  <div className="border-primary/30 absolute size-56 rounded-full border border-dashed" />
                  <div className="border-border absolute size-40 rounded-full border" />
                  <div className="bg-card absolute left-2 top-8 rounded-xl border p-3 shadow-lg">
                    <ChartNoAxesCombined className="text-primary size-5" />
                    <p className="mt-2 text-xs font-medium">Markets</p>
                  </div>
                  <div className="bg-card absolute bottom-6 right-0 rounded-xl border p-3 shadow-lg">
                    <LockKeyhole className="text-primary size-5" />
                    <p className="mt-2 text-xs font-medium">Security</p>
                  </div>
                  <div className="bg-card absolute right-3 top-3 rounded-xl border p-3 shadow-lg">
                    <Activity className="text-primary size-5" />
                    <p className="mt-2 text-xs font-medium">Insights</p>
                  </div>
                  <div className="border-primary/30 bg-primary text-primary-foreground shadow-primary/20 z-10 grid size-24 place-items-center rounded-3xl border shadow-xl">
                    <Waypoints className="size-9" />
                  </div>
                </div>
                <div className="bg-muted/30 mt-5 grid grid-cols-3 divide-x rounded-xl border py-3 text-center">
                  <div>
                    <p className="text-lg font-semibold">One</p>
                    <p className="text-muted-foreground text-xs">system</p>
                  </div>
                  <div>
                    <p className="text-lg font-semibold">Every</p>
                    <p className="text-muted-foreground text-xs">market</p>
                  </div>
                  <div>
                    <p className="text-lg font-semibold">$10</p>
                    <p className="text-muted-foreground text-xs">to begin</p>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </section>

      <section id="features" className="mx-auto max-w-7xl px-6 py-24 lg:px-8 lg:py-32">
        <div className="max-w-2xl">
          <p className="text-primary text-sm font-semibold uppercase tracking-[0.18em]">
            A better foundation
          </p>
          <h2 className="font-display mt-4 text-balance text-4xl font-semibold tracking-tight sm:text-5xl">
            Built around how investing should feel.
          </h2>
          <p className="text-muted-foreground mt-5 text-lg leading-8">
            Clear enough to start today. Powerful enough to grow with you for decades.
          </p>
        </div>
        <div className="mt-14 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {features.map(({ icon: Icon, title, description }, index) => (
            <Card
              key={title}
              className="hover:border-primary/40 group relative overflow-hidden p-6 transition-all hover:-translate-y-1 hover:shadow-xl"
            >
              <span className="font-display text-muted/80 absolute right-5 top-4 text-5xl font-semibold">
                0{index + 1}
              </span>
              <div className="relative">
                <span className="bg-primary/10 text-primary mb-10 grid size-11 place-items-center rounded-xl">
                  <Icon className="size-5" />
                </span>
                <h3 className="font-display text-lg font-semibold">{title}</h3>
                <p className="text-muted-foreground mt-3 text-sm leading-6">{description}</p>
              </div>
            </Card>
          ))}
        </div>
      </section>

      <section id="architecture" className="bg-secondary/40 border-y">
        <div className="mx-auto grid max-w-7xl gap-16 px-6 py-24 lg:grid-cols-2 lg:px-8 lg:py-32">
          <div className="flex flex-col justify-center">
            <p className="text-primary text-sm font-semibold uppercase tracking-[0.18em]">
              Platform architecture
            </p>
            <h2 className="font-display mt-4 text-balance text-4xl font-semibold tracking-tight sm:text-5xl">
              One system. Purpose-built layers.
            </h2>
            <p className="text-muted-foreground mt-6 max-w-xl text-lg leading-8">
              Atlas separates experience, intelligence, data, and infrastructure into secure,
              scalable layers—so each can evolve without compromising the whole.
            </p>
            <div className="mt-8 grid gap-4 text-sm sm:grid-cols-2">
              {[
                ["Composable", "Capabilities evolve independently."],
                ["Observable", "Health and performance are measurable."],
                ["Resilient", "Failures are isolated by design."],
                ["Secure", "Trust boundaries exist at every layer."],
              ].map(([title, description]) => (
                <div key={title} className="flex gap-3">
                  <Check className="text-primary mt-0.5 size-4 shrink-0" />
                  <div>
                    <p className="font-medium">{title}</p>
                    <p className="text-muted-foreground mt-1">{description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="space-y-3">
            {[
              {
                icon: Blocks,
                label: "Experience layer",
                detail: "Accessible, responsive interfaces",
              },
              {
                icon: Network,
                label: "Intelligence layer",
                detail: "Context, reasoning, and orchestration",
              },
              { icon: Database, label: "Data layer", detail: "Reliable, governed financial data" },
              {
                icon: LockKeyhole,
                label: "Trust layer",
                detail: "Identity, controls, and observability",
              },
            ].map(({ icon: Icon, label, detail }, index) => (
              <div
                key={label}
                className="bg-card hover:border-primary/40 group flex items-center gap-5 rounded-2xl border p-5 shadow-sm transition-colors"
              >
                <span className="bg-primary/10 text-primary grid size-12 shrink-0 place-items-center rounded-xl">
                  <Icon className="size-5" />
                </span>
                <div className="flex-1">
                  <p className="font-display font-semibold">{label}</p>
                  <p className="text-muted-foreground mt-1 text-sm">{detail}</p>
                </div>
                <span className="text-muted-foreground font-mono text-xs">L{index + 1}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="roadmap" className="mx-auto max-w-7xl px-6 py-24 lg:px-8 lg:py-32">
        <div className="text-center">
          <p className="text-primary text-sm font-semibold uppercase tracking-[0.18em]">
            The journey ahead
          </p>
          <h2 className="font-display mt-4 text-4xl font-semibold tracking-tight sm:text-5xl">
            Built deliberately. Scaled responsibly.
          </h2>
        </div>
        <div className="relative mt-16 grid gap-5 lg:grid-cols-3">
          <div className="border-primary/30 absolute left-[16%] right-[16%] top-8 hidden border-t border-dashed lg:block" />
          {roadmap.map((item, index) => (
            <div key={item.phase} className="bg-card relative rounded-2xl border p-7">
              <div className="mb-8 flex items-center justify-between">
                <span className="border-primary/30 bg-background text-primary grid size-9 place-items-center rounded-full border font-mono text-xs">
                  0{index + 1}
                </span>
                <span className="bg-primary/10 text-primary rounded-full px-2.5 py-1 text-xs font-medium">
                  {item.status}
                </span>
              </div>
              <h3 className="font-display text-xl font-semibold">{item.phase}</h3>
              <p className="text-muted-foreground mt-3 leading-7">{item.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="px-6 pb-24 lg:px-8">
        <div className="bg-primary text-primary-foreground relative mx-auto max-w-7xl overflow-hidden rounded-3xl px-6 py-16 text-center sm:px-12">
          <div className="absolute inset-0 opacity-10 [background-image:radial-gradient(circle_at_center,white_1px,transparent_1px)] [background-size:24px_24px]" />
          <div className="relative">
            <h2 className="font-display text-balance text-3xl font-semibold sm:text-5xl">
              A more intelligent financial future starts here.
            </h2>
            <p className="text-primary-foreground/75 mx-auto mt-5 max-w-2xl">
              Join us as we build investment infrastructure for everyone.
            </p>
            <Button size="lg" variant="secondary" className="mt-8" asChild>
              <a href="#roadmap">
                View the roadmap <ArrowRight className="size-4" />
              </a>
            </Button>
          </div>
        </div>
      </section>

      <footer className="border-t">
        <div className="mx-auto flex max-w-7xl flex-col gap-8 px-6 py-10 sm:flex-row sm:items-center sm:justify-between lg:px-8">
          <div className="flex items-center gap-2.5">
            <span className="bg-primary text-primary-foreground grid size-8 place-items-center rounded-lg">
              <Waypoints className="size-4" />
            </span>
            <span className="font-display font-semibold">Atlas AI</span>
          </div>
          <p className="text-muted-foreground text-sm">
            © 2026 Atlas AI. Building the future of investing.
          </p>
          <div
            className="text-muted-foreground flex gap-5 text-sm"
            aria-label="Platform principles"
          >
            <span>Privacy</span>
            <span>Security</span>
            <span>Clarity</span>
          </div>
        </div>
      </footer>
    </main>
  );
}
