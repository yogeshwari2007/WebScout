import { Hero } from "@/components/landing/Hero";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { ComparisonVsOthers } from "@/components/landing/ComparisonVsOthers";
import { FeatureGrid } from "@/components/landing/FeatureGrid";
import { FinalCTA } from "@/components/landing/FinalCTA";

export default function LandingPage() {
  return (
    <div className="flex flex-col w-full selection:bg-primary/20 selection:text-foreground">
      <Hero />
      <HowItWorks />
      <ComparisonVsOthers />
      <FeatureGrid />
      <FinalCTA />
    </div>
  );
}
