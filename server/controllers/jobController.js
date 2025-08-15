require("dotenv").config();
const Job = require("../models/Job");
const axios = require("axios");
const cloudinary = require("cloudinary").v2;
const fs = require("fs");

cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key: process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET,
});

exports.uploadJob = async (req, res) => {
  const filePath = req.file.path;
  const result = await cloudinary.uploader.upload(filePath, { resource_type: "raw" });

  const aiRes = await axios.post(process.env.AI_URL, { pdf_url: result.secure_url });
  const { company, role, deadline } = aiRes.data;

  const job = await Job.create({ pdfUrl: result.secure_url, company, role, deadline });
  fs.unlinkSync(filePath);

  res.json(job);
};

exports.getJobs = async (req, res) => {
  const jobs = await Job.find();
  res.json(jobs);
};

exports.updateStatus = async (req, res) => {
  const { id } = req.params;
  const { status } = req.body;
  const job = await Job.findByIdAndUpdate(id, { status }, { new: true });
  res.json(job);
};

exports.editJob = async (req, res) => {
  const { id } = req.params;
  const { company, role, deadline } = req.body;
  try {
    const job = await Job.findByIdAndUpdate(
      id,
      { company, role, deadline },
      { new: true }
    );
    res.json(job);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Server error" });
  }
};


exports.deleteJob = async (req, res) => {
  const { id } = req.params;
  await Job.findByIdAndDelete(id);
  res.json({ success: true });
};
