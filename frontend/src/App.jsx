import { useEffect, useState } from "react";
import FileUpload from "./components/FileUpload";
import JobTable from "./components/JobTable";
import axios from "axios";

function App() {
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    axios.get("http://localhost:5000/api/jobs").then(res => setJobs(res.data));
  }, []);

  const handleStatusChange = async (id, newStatus) => {
    await axios.patch(`http://localhost:5000/api/jobs/${id}`, { status: newStatus });
    setJobs(jobs.map(job => job._id === id ? { ...job, status: newStatus } : job));
  };

  const handleDelete = async (id) => {
    await axios.delete(`http://localhost:5000/api/jobs/${id}`);
    setJobs(jobs.filter(job => job._id !== id));
  };

  const handleEdit = async (id, editFields) => {
  await axios.patch(`http://localhost:5000/api/jobs/${id}/edit`, editFields);
  // refresh
  const updated = await axios.get("http://localhost:5000/api/jobs");
  setJobs(updated.data);
};


  return (
    <div className="min-h-screen bg-cover bg-center bg-no-repeat text-gray-800" style={{ backgroundImage: "url('/background.jpg')", backgroundAttachment: "fixed" }}>
      <header className="bg-white/80 backdrop-blur-md shadow-md py-6 mb-8 border-b border-white/20">
        <div className="max-w-6xl mx-auto px-4">
          <h1 className="text-3xl font-extrabold text-blue-600">📄 Job Deadline Extractor</h1>
          <p className="text-sm text-gray-500 mt-1">Upload job description PDFs and track your applications easily.</p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 pb-12">
        <section className="mb-10 bg-white/80 backdrop-blur-md p-6 rounded-xl shadow-sm border border-white/20">
          <h2 className="text-xl font-semibold mb-4 text-gray-700">Upload Job Description</h2>
          <FileUpload onUploadSuccess={(job) => setJobs([...jobs, job])} />
        </section>

        <section className="bg-white/80 backdrop-blur-md p-6 rounded-xl shadow-sm border border-white/20">
          <h2 className="text-xl font-semibold mb-4 text-gray-700">Your Applications</h2>
          <JobTable
            jobs={jobs}
            onStatusChange={handleStatusChange}
            onDelete={handleDelete}
            onEdit={handleEdit}
          />
        </section>

      </main>
    </div>
  );
}

export default App;
