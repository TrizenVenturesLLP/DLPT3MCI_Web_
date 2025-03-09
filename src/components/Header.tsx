import { Shield } from "lucide-react";

export const Header = () => {
  return (
    <header className="bg-police-dark text-white p-6 shadow-lg">
      <div className="container mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Shield className="w-8 h-8" />
          <h1 className="text-2xl font-bold">Missing Child Identification System</h1>
        </div>
        <nav>
          <ul className="flex space-x-6">
            <li>
              <a href="#report-missing" className="hover:text-police-blue transition-colors">
                Report Missing
              </a>
            </li>
            <li>
              <a href="#report-found" className="hover:text-police-blue transition-colors">
                Report Found
              </a>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
};