const mongoose = require("mongoose");

const jobSchema = new mongoose.Schema({
  pdfUrl: String,
  company: String,
  role: String,
  deadline: String,
  status: { type: String, default: "Not Yet Applied" },
}, { timestamps: true });

module.exports = mongoose.model("Job", jobSchema);
