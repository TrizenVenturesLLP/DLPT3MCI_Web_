import { Header } from "@/components/Header";
import { ReportMissingSection } from "@/components/ReportMissingSection";
import { ReportFoundSection } from "@/components/ReportFoundSection";

const Index = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="container mx-auto px-4 py-8 space-y-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <ReportMissingSection />
          <ReportFoundSection />
        </div>
      </main>
    </div>
  );
};

export default Index;