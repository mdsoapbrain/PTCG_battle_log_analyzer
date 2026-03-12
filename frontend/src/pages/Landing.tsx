import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Zap, FileText, History, BarChart3, GitCompareArrows, ArrowUpDown } from "lucide-react";
import { motion } from "framer-motion";

const features = [
  { icon: FileText, title: "Paste & Parse", desc: "Drop your raw battle log and get instant structured analysis." },
  { icon: History, title: "Track History", desc: "Build your competitive record over time with every match." },
  { icon: BarChart3, title: "Deck Analytics", desc: "See win rates, trends, and performance by deck archetype." },
  { icon: GitCompareArrows, title: "Matchup Intel", desc: "Understand how your decks perform against the meta." },
  { icon: ArrowUpDown, title: "First vs Second", desc: "Know your edge when going first or second." },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent" />
        <div className="relative max-w-5xl mx-auto px-6 pt-20 pb-24 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 mb-6 px-3 py-1 rounded-full border border-primary/30 bg-primary/5">
              <Zap className="h-3.5 w-3.5 text-primary" />
              <span className="text-xs font-medium text-primary">Battle Intelligence Platform</span>
            </div>
            <h1 className="text-5xl md:text-6xl font-bold font-display tracking-tight mb-5">
              <span className="text-gradient-primary">PTCG Battle Intel</span>
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-8 leading-relaxed">
              Turn raw Pokémon TCG Live battle logs into competitive intelligence.
              Track win rates, analyze deck performance, and master your matchups.
            </p>
            <div className="flex items-center justify-center gap-3">
              <Button asChild size="lg" className="gradient-primary font-semibold">
                <Link to="/signin">Get Started</Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link to="/signup">Create Account</Link>
              </Button>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Features */}
      <div className="max-w-5xl mx-auto px-6 pb-24">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 + i * 0.08 }}
              className="rounded-lg border border-border bg-card p-5 hover:border-primary/30 transition-colors"
            >
              <f.icon className="h-5 w-5 text-primary mb-3" />
              <h3 className="font-display font-semibold text-foreground mb-1">{f.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-border py-6 text-center text-xs text-muted-foreground">
        PTCG Battle Intel — Not affiliated with The Pokémon Company or Nintendo.
      </footer>
    </div>
  );
}
