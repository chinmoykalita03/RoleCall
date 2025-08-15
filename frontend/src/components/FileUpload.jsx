import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { UploadCloud } from 'lucide-react';

function FileUpload({ onUploadSuccess }) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'application/pdf': [] },
    onDrop: async (acceptedFiles) => {
      const formData = new FormData();
      formData.append("file", acceptedFiles[0]);

      try {
        const res = await axios.post("http://localhost:5000/api/upload", formData);
        onUploadSuccess(res.data);
      } catch (err) {
        console.error("Upload failed", err);
        alert("Upload failed. See console for details.");
      }
    }
  });

  return (
    <div {...getRootProps()} className={`p-6 border-2 border-dashed rounded-lg text-center cursor-pointer bg-white shadow-sm transition-all duration-300 ${isDragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300'}`}>
      <input {...getInputProps()} />
      <div className="flex flex-col items-center justify-center">
        <UploadCloud className="h-10 w-10 text-blue-500 mb-2" />
        <p className="text-gray-600">
          Drag and drop a <span className="font-semibold text-blue-600">PDF</span> file here, or click to select one.
        </p>
      </div>
    </div>
  );
}

export default FileUpload;
