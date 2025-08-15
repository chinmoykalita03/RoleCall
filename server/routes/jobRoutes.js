const express = require("express");
const router = express.Router();
const multer = require("multer");
const upload = multer({ dest: "uploads/" });
const controller = require("../controllers/jobController");

router.post("/upload", upload.single("file"), controller.uploadJob);
router.get("/jobs", controller.getJobs);
router.patch("/jobs/:id", controller.updateStatus);
router.patch("/jobs/:id/edit", controller.editJob);
router.delete("/jobs/:id", controller.deleteJob);

module.exports = router;
