/**
 * SwarmAI Logo Component
 *
 * Reusable logo component with different variants and sizes.
 */

import React from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";

interface SwarmAILogoProps {
  variant?: "logo-only" | "logo-with-name";
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
  priority?: boolean;
}

const sizeConfig = {
  sm: { width: 24, height: 24 },
  md: { width: 40, height: 40 },
  lg: { width: 60, height: 60 },
  xl: { width: 120, height: 40 },
};

export function SwarmAILogo({
  variant = "logo-with-name",
  size = "md",
  className,
  priority = false,
}: SwarmAILogoProps) {
  const logoSrc =
    variant === "logo-only"
      ? "/swarm-ai-logo.png"
      : "/swarm-ai-logo-with-name.png";

  const dimensions =
    variant === "logo-with-name" && size !== "sm"
      ? { width: sizeConfig.xl.width, height: sizeConfig.xl.height }
      : sizeConfig[size];

  return (
    <Image
      src={logoSrc}
      alt="SwarmAI"
      width={dimensions.width}
      height={dimensions.height}
      className={cn("object-contain", className)}
      priority={priority}
    />
  );
}

export default SwarmAILogo;
