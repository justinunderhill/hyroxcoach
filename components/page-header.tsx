import Link from "next/link";

type PageHeaderProps = {
  eyebrow: string;
  title: string;
  href?: string;
  size?: "md" | "lg";
};

export function PageHeader({ eyebrow, title, href = "/dashboard", size = "lg" }: PageHeaderProps) {
  return (
    <div className="flex items-start justify-between">
      <div>
        <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-lime">{eyebrow}</p>
        <h1
          className={
            size === "lg"
              ? "mt-1 text-3xl font-semibold tracking-[-0.045em] text-ink"
              : "mt-1 text-2xl font-semibold tracking-[-0.045em] text-ink"
          }
        >
          {title}
        </h1>
      </div>
      <Link className="text-xs font-semibold text-muted" href={href}>
        Close
      </Link>
    </div>
  );
}
