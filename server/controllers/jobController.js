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
  let filePath = null;
  try {
    filePath = req.file.path;
    console.log(`📤 Uploading file to Cloudinary: ${filePath}`);
    const result = await cloudinary.uploader.upload(filePath, { resource_type: "raw" });
    console.log(`✅ Cloudinary upload successful: ${result.secure_url}`);

    let company = "Unknown";
    let role = "Unknown";
    let deadline = "Not Found";

    try {
      console.log(`🤖 Sending text extraction request to AI service: ${process.env.AI_URL}`);
      const aiRes = await axios.post(process.env.AI_URL, { pdf_url: result.secure_url }, { timeout: 45000 });
      if (aiRes.data) {
        company = aiRes.data.company || "Unknown";
        role = aiRes.data.role || "Unknown";
        deadline = aiRes.data.deadline || "Not Found";
        console.log(`✅ AI extraction successful:`, aiRes.data);
      }
    } catch (aiErr) {
      console.error(`⚠️ AI extraction failed or timed out: ${aiErr.message}. Falling back to default values.`);
    }

    const job = await Job.create({ pdfUrl: result.secure_url, company, role, deadline });
    
    // Clean up local temp file
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }

    res.json(job);
  } catch (err) {
    console.error(`❌ Upload error:`, err);
    if (filePath && fs.existsSync(filePath)) {
      try { fs.unlinkSync(filePath); } catch (e) {}
    }
    res.status(500).json({ error: "Failed to upload and parse job description PDF." });
  }
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
