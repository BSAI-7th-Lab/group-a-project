import { Button as BaseButton } from "@base-ui/react/button";
import { cva, type VariantProps } from "class-variance-authority";
import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex h-11 items-center justify-center rounded-lg px-5 text-sm font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-emerald-400 text-slate-950 hover:bg-emerald-300",
        outline:
          "border border-slate-600 bg-transparent text-white hover:bg-slate-800",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

type ButtonProps = ComponentProps<typeof BaseButton> &
  VariantProps<typeof buttonVariants>;

export function Button({ className, variant, ...props }: ButtonProps) {
  return (
    <BaseButton
      className={cn(buttonVariants({ variant }), className)}
      {...props}
    />
  );
}
