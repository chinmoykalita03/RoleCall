import { useState } from "react";

function JobTable({ jobs, onStatusChange, onDelete, onEdit }) {
  const [editId, setEditId] = useState(null);
  const [editFields, setEditFields] = useState({
    company: "",
    role: "",
    deadline: ""
  });

  if (jobs.length === 0) {
    return <p className="text-gray-500">No applications added yet. Upload a PDF to get started.</p>;
  }

  const startEdit = (job) => {
    setEditId(job._id);
    setEditFields({
      company: job.company || "",
      role: job.role || "",
      deadline: job.deadline || "",
    });
  };

  const saveEdit = async (id) => {
    await onEdit(id, editFields);
    setEditId(null);
  };

  return (
    <div className="overflow-x-auto rounded-lg shadow-lg bg-gradient-to-br from-white to-gray-50 border border-gray-200">
      <table className="min-w-full text-sm text-left rounded-lg overflow-hidden">
        <thead className="bg-gradient-to-r from-blue-100 to-blue-200 text-gray-700 uppercase text-xs tracking-wider border-b border-gray-300">
          <tr>
            <th className="px-4 py-3">#</th>
            <th className="px-4 py-3">Company</th>
            <th className="px-4 py-3">Role</th>
            <th className="px-4 py-3">Deadline</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Action</th>
          </tr>
        </thead>
        <tbody className="text-gray-800">
          {jobs.map((job, i) => (
            <tr
              key={job._id}
              className={`border-t transition
                ${i % 2 === 0 ? "bg-gray-50" : "bg-white"}
                hover:bg-blue-50
              `}
            >
              <td className="px-4 py-3 font-semibold">{i + 1}</td>

              {/* company */}
              <td className="px-4 py-3">
                {editId === job._id ? (
                  <input
                    value={editFields.company}
                    onChange={(e) => setEditFields({ ...editFields, company: e.target.value })}
                    className="border px-2 py-1 rounded w-full"
                  />
                ) : (
                  job.company || "Unknown"
                )}
              </td>

              {/* role */}
              <td className="px-4 py-3">
                {editId === job._id ? (
                  <input
                    value={editFields.role}
                    onChange={(e) => setEditFields({ ...editFields, role: e.target.value })}
                    className="border px-2 py-1 rounded w-full"
                  />
                ) : (
                  job.role || "Unknown"
                )}
              </td>

              {/* deadline */}
              <td className="px-4 py-3">
                {editId === job._id ? (
                  <input
                    type="date"
                    value={editFields.deadline}
                    onChange={(e) => setEditFields({ ...editFields, deadline: e.target.value })}
                    className="border px-2 py-1 rounded"
                  />
                ) : (
                  <span className="text-blue-700 font-semibold">{job.deadline}</span>
                )}
              </td>

              {/* status */}
              <td className="px-4 py-3">
                <select
                  value={job.status}
                  onChange={(e) => onStatusChange(job._id, e.target.value)}
                  className={`border text-sm px-2 py-1 rounded shadow
                    ${job.status === "Applied"
                      ? "bg-green-100 border-green-300 text-green-700"
                      : "bg-red-100 border-red-300 text-red-700"}`}
                >
                  <option value="Not Yet Applied">Not Yet Applied</option>
                  <option value="Applied">Applied</option>
                </select>
              </td>

              {/* actions */}
              <td className="px-4 py-3 space-x-2">
                {editId === job._id ? (
                  <button
                    onClick={() => saveEdit(job._id)}
                    className="text-green-600 hover:text-green-800 font-semibold text-sm"
                  >
                    Save
                  </button>
                ) : (
                  <button
                    onClick={() => startEdit(job)}
                    className="text-blue-600 hover:text-blue-800 font-semibold text-sm"
                  >
                    Edit
                  </button>
                )}
                <button
                  onClick={() => onDelete(job._id)}
                  className="text-red-600 hover:text-red-800 font-semibold text-sm"
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default JobTable;
