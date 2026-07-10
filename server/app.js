const express = require("express");
const mongoose = require("mongoose");
const dotenv = require("dotenv");
const jobRoutes = require("./routes/jobRoutes");
const cors = require("cors");

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// ✅ MongoDB Connection
mongoose.connect(process.env.MONGO_URI)
  .then(() => {
    app.listen(PORT, () => {
      console.log(`✅ MongoDB connected`);
      console.log(`🚀 Server running at http://localhost:${PORT}`);
    });
  })
  .catch((err) => {
    console.error('❌ DB connection error:', err.message);
    process.exit(1); // Exit on failure
  });

// Routes
app.use("/api", jobRoutes);