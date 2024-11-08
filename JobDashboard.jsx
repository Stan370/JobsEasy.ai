import { useState, useEffect } from 'react';
import { useJobMatches } from '../hooks/useJobMatches';
import JobCard from './JobCard';

export default function JobDashboard() {
  const { jobs, loading, error } = useJobMatches();
  const [filters, setFilters] = useState({
    minSalary: 0,
    maxDistance: 50,
    remote: false,
  });

  return (
    <div className="container mx-auto p-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {jobs.map(job => (
          <JobCard 
            key={job.id} 
            job={job}
            onApply={() => handleQuickApply(job)}
          />
        ))}
      </div>
    </div>
  );
} 