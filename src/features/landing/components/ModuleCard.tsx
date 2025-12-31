// src/features/landing/components/ModuleCard.tsx
import { useNavigate } from 'react-router-dom'; // <-- 1. Import

// 2. Update the 'module' prop shape
interface Module {
    id: string;
    name: string;
    icon: string;
    description: string;
    path: string; // <-- Add path
}

interface ModuleCardProps {
    module: Module;
    // onNavigate: (id: string) => void; // <-- 3. REMOVE onNavigate
}

// 4. Apply props and add hook
export const ModuleCard = ({ module }: ModuleCardProps) => {
    const navigate = useNavigate(); // <-- 5. Use the hook

    return (
        <div
            className="hover:shadow-lg transition-shadow cursor-pointer bg-white rounded-lg border border-slate-200"
            onClick={() => navigate(module.path)} // <-- 6. Use navigate
        >
            <div className="p-8">
                <div className="flex items-start gap-4">
                    <div className="text-5xl">{module.icon}</div>
                    <div className="flex-1">
                        <h3 className="text-xl font-bold text-slate-900">{module.name}</h3>
                        <p className="text-slate-600 text-sm mt-2">{module.description}</p>
                        <button
                            tabIndex={-1} // Makes the button not focusable
                            className="mt-4 px-4 py-2 bg-slate-900 text-white text-sm font-semibold rounded-md hover:bg-slate-800"
                        >
                            Abrir Modulo
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};