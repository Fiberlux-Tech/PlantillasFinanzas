// src/components/shared/StatsCard.tsx
import React from 'react';

// 1. Define the props interface
interface StatsCardProps {
    title: string;
    value: string | number;
    icon: React.ReactNode; // Type as ReactNode to accept icon components
    iconBgColor: string;
}

// 2. Apply the props interface
function StatsCard({ title, value, icon, iconBgColor }: StatsCardProps) {
    return (
        <div className="bg-white p-6 rounded-lg shadow-sm flex items-center">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${iconBgColor}`}>{icon}</div>
            <div className="ml-4">
                <p className="text-sm text-gray-500">{title}</p>
                <p className="text-2xl font-bold text-gray-800">{value}</p>
            </div>
        </div>
    );
}

export default StatsCard;