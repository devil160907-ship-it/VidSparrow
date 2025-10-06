// script.js - Complete JavaScript for Video Downloader with Quality Selector

class VidSparrow {
  constructor() {
    this.currentPlatform = "youtube";
    this.currentMediaType = "mp4";
    this.currentQuality = "best";
    this.currentVideoInfo = null;
    this.initializeEventListeners();
    this.loadRecentDownloads();
  }

  initializeEventListeners() {
    console.log("Initializing event listeners...");

    // Platform tabs
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        this.switchPlatform(e.currentTarget.dataset.platform);
      });
    });

    // Media type tabs
    document.querySelectorAll(".media-tab-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        this.switchMediaType(e.currentTarget.dataset.mediaType);
      });
    });

    // Preview button
    const previewBtn = document.getElementById("previewBtn");
    if (previewBtn) {
      previewBtn.addEventListener("click", () => {
        this.previewVideo();
      });
      console.log("Preview button event listener added");
    } else {
      console.error("Preview button not found!");
    }

    // Download button
    const downloadBtn = document.getElementById("downloadBtn");
    if (downloadBtn) {
      downloadBtn.addEventListener("click", () => {
        this.downloadMedia();
      });
    }

    // Enter key in URL input
    const urlInput = document.getElementById("videoUrl");
    if (urlInput) {
      urlInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
          this.previewVideo();
        }
      });

      // Auto-detect platform from URL input
      urlInput.addEventListener("input", (e) => {
        this.autoDetectPlatform(e.target.value);
      });

      // Clear preview when URL changes
      urlInput.addEventListener("input", () => {
        this.clearPreview();
      });
    }

    // Initialize quality selector
    this.initializeQualitySelector();
  }

  initializeQualitySelector() {
    // Create quality selector HTML if it doesn't exist
    if (!document.getElementById("qualitySelector")) {
      const downloadSection = document.querySelector(".download-section");
      const qualitySelectorHTML = `
        <div id="qualitySelector" class="quality-selector hidden">
          <h4>Select Quality:</h4>
          <div id="qualityOptions" class="quality-options">
            <!-- Quality options will be dynamically populated here -->
          </div>
        </div>
      `;

      const videoPreview = document.getElementById("videoPreview");
      if (videoPreview && videoPreview.parentNode) {
        videoPreview.parentNode.insertAdjacentHTML(
          "beforebegin",
          qualitySelectorHTML
        );
      }
    }
  }

  autoDetectPlatform(url) {
    if (!url.trim()) return;

    // Simple platform detection based on URL patterns
    if (url.includes("youtube.com") || url.includes("youtu.be")) {
      if (this.currentPlatform !== "youtube") {
        this.switchPlatform("youtube");
      }
    } else if (url.includes("instagram.com")) {
      if (this.currentPlatform !== "instagram") {
        this.switchPlatform("instagram");
      }
    }
  }

  switchPlatform(platform) {
    console.log("Switching platform to:", platform);
    this.currentPlatform = platform;

    // Update active tab
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.platform === platform);
    });

    // Clear previous data
    this.clearPreview();
    this.updatePlaceholder();
    this.updateQualityOptions();
  }

  switchMediaType(mediaType) {
    console.log("Switching media type to:", mediaType);
    this.currentMediaType = mediaType;

    // Update active tab
    document.querySelectorAll(".media-tab-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.mediaType === mediaType);
    });

    // Update quality options when media type changes
    this.updateQualityOptions();
  }

  updatePlaceholder() {
    const input = document.getElementById("videoUrl");
    if (input) {
      const examples = {
        youtube: "e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        instagram: "e.g., https://www.instagram.com/p/Cxyz123456/",
      };
      input.placeholder = `Paste ${this.currentPlatform} link here... ${
        examples[this.currentPlatform]
      }`;
    }
  }

  updateQualityOptions() {
    const qualityOptions = this.getQualityOptions(
      this.currentMediaType,
      this.currentPlatform
    );
    this.populateQualityOptions(qualityOptions);
  }

  getQualityOptions(mediaType, platform) {
    if (mediaType === "mp3") {
      return [
        { value: "best", label: "Best Quality (320kbps)" },
        { value: "192k", label: "High Quality (192kbps)" },
        { value: "128k", label: "Good Quality (128kbps)" },
        { value: "64k", label: "Standard Quality (64kbps)" },
      ];
    } else {
      if (platform === "youtube") {
        return [
          { value: "best", label: "Best Available (up to 1080p)" },
          { value: "1080p", label: "Full HD (1080p)" },
          { value: "720p", label: "HD (720p)" },
          { value: "480p", label: "Standard (480p)" },
          { value: "360p", label: "Low (360p)" },
        ];
      } else {
        return [
          { value: "best", label: "Best Available" },
          { value: "720p", label: "HD (720p)" },
          { value: "480p", label: "Standard (480p)" },
        ];
      }
    }
  }

  populateQualityOptions(qualityOptions) {
    const qualityContainer = document.getElementById("qualityOptions");
    const qualitySelector = document.getElementById("qualitySelector");

    if (!qualityContainer || !qualitySelector) return;

    if (!qualityOptions || qualityOptions.length === 0) {
      qualitySelector.classList.add("hidden");
      return;
    }

    qualityContainer.innerHTML = "";

    qualityOptions.forEach((option) => {
      const qualityBtn = document.createElement("button");
      qualityBtn.type = "button";
      qualityBtn.className = "quality-option";
      qualityBtn.textContent = option.label;
      qualityBtn.dataset.value = option.value;

      if (option.value === this.currentQuality) {
        qualityBtn.classList.add("selected");
      }

      qualityBtn.addEventListener("click", () => {
        // Remove selected class from all options
        document.querySelectorAll(".quality-option").forEach((btn) => {
          btn.classList.remove("selected");
        });

        // Add selected class to clicked option
        qualityBtn.classList.add("selected");
        this.currentQuality = qualityBtn.dataset.value;

        // Update download button with quality info
        this.updateDownloadButton();
      });

      qualityContainer.appendChild(qualityBtn);
    });

    // Only show quality selector if we have a video preview
    if (this.currentVideoInfo) {
      qualitySelector.classList.remove("hidden");
    }
  }

  hideQualitySelector() {
    const qualitySelector = document.getElementById("qualitySelector");
    if (qualitySelector) {
      qualitySelector.classList.add("hidden");
    }
  }

  updateDownloadButton() {
    const downloadBtn = document.getElementById("downloadBtn");
    if (downloadBtn && this.currentVideoInfo) {
      downloadBtn.disabled = false;
      // Optional: Update button text to show selected quality
      // downloadBtn.innerHTML = `<i class="fas fa-download"></i> Download (${this.getQualityLabel()})`;
    }
  }

  getQualityLabel() {
    const qualityOptions = this.getQualityOptions(
      this.currentMediaType,
      this.currentPlatform
    );
    const currentOption = qualityOptions.find(
      (opt) => opt.value === this.currentQuality
    );
    return currentOption
      ? currentOption.label.split("(")[0].trim()
      : this.currentQuality;
  }

  async previewVideo() {
    console.log("Preview button clicked");

    const urlInput = document.getElementById("videoUrl");
    if (!urlInput) {
      this.showError("URL input not found");
      return;
    }

    const url = urlInput.value.trim();

    if (!url) {
      this.showError("Please enter a video URL");
      return;
    }

    // Basic URL validation
    if (!this.isValidUrl(url)) {
      this.showError(
        "Please enter a valid URL starting with http:// or https://"
      );
      return;
    }

    this.showLoading("Getting video info...");

    try {
      console.log("Sending request to /get-video-info");
      const response = await fetch("/get-video-info", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: url,
          platform: this.currentPlatform,
        }),
      });

      console.log("Response received:", response.status);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Video info data:", data);

      if (data.success) {
        this.currentVideoInfo = data;
        this.displayPreview(data);
        this.updateQualityOptions(); // Show quality options after successful preview
      } else {
        this.showError(data.error || "Failed to get video information");
        this.clearPreview();
      }
    } catch (error) {
      console.error("Preview error:", error);
      this.showError(
        "Network error. Please check your connection and try again."
      );
      this.clearPreview();
    } finally {
      this.hideLoading();
    }
  }

  displayPreview(info) {
    console.log("Displaying preview:", info);
    const preview = document.getElementById("videoPreview");
    const thumbnail = document.getElementById("previewThumbnail");
    const title = document.getElementById("previewTitle");
    const uploader = document.getElementById("previewUploader");
    const duration = document.getElementById("previewDuration");
    const views = document.getElementById("previewViews");

    if (!preview || !thumbnail || !title || !uploader || !duration || !views) {
      console.error("Preview elements not found");
      return;
    }

    // Set thumbnail with fallback
    if (info.thumbnail) {
      thumbnail.src = info.thumbnail;
      thumbnail.onerror = function () {
        this.src = "/static/images/default-thumbnail.jpg";
      };
    } else {
      thumbnail.src = "/static/images/default-thumbnail.jpg";
    }

    title.textContent = info.title || "Unknown Title";
    uploader.textContent = `By: ${info.uploader || "Unknown"}`;
    duration.textContent = `Duration: ${this.formatDuration(info.duration)}`;
    views.textContent = `Views: ${this.formatViews(info.view_count)}`;

    preview.classList.remove("hidden");

    // Show quality selector and enable download button
    const qualitySelector = document.getElementById("qualitySelector");
    if (qualitySelector) {
      qualitySelector.classList.remove("hidden");
    }

    this.updateDownloadButton();
  }

  clearPreview() {
    const preview = document.getElementById("videoPreview");
    const downloadBtn = document.getElementById("downloadBtn");

    if (preview) {
      preview.classList.add("hidden");
    }
    if (downloadBtn) {
      downloadBtn.disabled = true;
    }

    this.hideQualitySelector();
    this.currentVideoInfo = null;
  }

  async downloadMedia() {
    const urlInput = document.getElementById("videoUrl");
    if (!urlInput || !this.currentVideoInfo) {
      this.showError("Please preview the video first");
      return;
    }

    const url = urlInput.value.trim();

    this.showProgress("Starting download...");

    try {
      console.log("Sending download request...");
      const response = await fetch("/download", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: url,
          platform: this.currentPlatform,
          media_type: this.currentMediaType,
          quality: this.currentQuality, // Include quality parameter
        }),
      });

      console.log("Download response status:", response.status);
      const data = await response.json();
      console.log("Download response data:", data);

      if (data.success) {
        this.updateProgress("Download completed! Preparing file...", 100);

        // Wait a moment then trigger download
        setTimeout(() => {
          if (data.filename) {
            // Create download link
            const downloadUrl = `/download-file/${encodeURIComponent(
              data.filename
            )}`;
            console.log("Downloading file:", downloadUrl);

            // Create temporary link and click it
            const link = document.createElement("a");
            link.href = downloadUrl;
            link.download = data.filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            this.showToast(
              `Download started successfully! (Quality: ${this.getQualityLabel()})`,
              "success"
            );
          } else {
            this.showError("Download completed but no filename returned");
          }

          this.hideProgress();
          this.loadRecentDownloads();
          this.clearForm();
        }, 1000);
      } else {
        const errorMsg = data.error || "Download failed";
        console.error("Download failed:", errorMsg);

        // Handle FFmpeg specific error
        if (errorMsg.includes("FFmpeg") || errorMsg.includes("ffprobe")) {
          this.showError(
            "FFmpeg is required for audio conversion. " +
              "Please install FFmpeg on your system or download as MP4 video instead. " +
              "Check the documentation for installation instructions."
          );
        } else {
          this.showError(errorMsg);
        }
        this.hideProgress();
      }
    } catch (error) {
      console.error("Download error:", error);
      this.showError(
        "Network error. Please check your connection and try again."
      );
      this.hideProgress();
    }
  }

  async loadRecentDownloads() {
    try {
      const response = await fetch("/api/downloads");
      const downloads = await response.json();

      const container = document.getElementById("recentDownloadsList");
      if (!container) return;

      if (downloads.length === 0) {
        container.innerHTML =
          '<div class="no-downloads">No recent downloads</div>';
        return;
      }

      container.innerHTML = downloads
        .slice(0, 10)
        .map(
          (download) => `
                <div class="download-item" data-download-id="${download.id}">
                    <div class="download-thumbnail">
                        <img src="${
                          download.thumbnail_url ||
                          "/static/images/default-thumbnail.jpg"
                        }" 
                             alt="${
                               download.video_title
                             }" onerror="this.src='/static/images/default-thumbnail.jpg'">
                        <div class="platform-badge ${download.platform}">
                            <i class="fab fa-${download.platform}"></i>
                        </div>
                    </div>
                    <div class="download-info">
                        <h3 class="download-title">${this.truncateText(
                          download.video_title,
                          50
                        )}</h3>
                        <div class="download-meta">
                            <span class="media-type ${download.media_type}">
                                ${download.media_type.toUpperCase()}
                            </span>
                            <span class="download-date">
                                ${new Date(
                                  download.downloaded_at
                                ).toLocaleDateString()} at ${new Date(
            download.downloaded_at
          ).toLocaleTimeString()}
                            </span>
                            <span class="platform ${download.platform}">
                                ${download.platform}
                            </span>
                        </div>
                    </div>
                    <div class="download-actions">
                        <button class="delete-btn" onclick="vidSparrow.deleteDownload('${
                          download.id
                        }')" 
                                title="Delete from history">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `
        )
        .join("");

      // Add clear all button if there are downloads
      this.addClearAllButton();
    } catch (error) {
      console.error("Error loading recent downloads:", error);
    }
  }

  async deleteDownload(downloadId) {
    if (
      !confirm("Are you sure you want to delete this download from history?")
    ) {
      return;
    }

    try {
      const response = await fetch(`/delete-download/${downloadId}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const data = await response.json();

      if (data.success) {
        this.showToast("Download deleted successfully", "success");
        this.loadRecentDownloads(); // Refresh the list
      } else {
        this.showError(data.error || "Failed to delete download");
      }
    } catch (error) {
      console.error("Delete error:", error);
      this.showError("Network error. Please try again.");
    }
  }

  async clearAllDownloads() {
    if (
      !confirm(
        "Are you sure you want to clear ALL download history? This action cannot be undone."
      )
    ) {
      return;
    }

    try {
      const response = await fetch("/clear-all-downloads", {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const data = await response.json();

      if (data.success) {
        this.showToast(`All downloads cleared successfully`, "success");
        this.loadRecentDownloads(); // Refresh the list
      } else {
        this.showError(data.error || "Failed to clear downloads");
      }
    } catch (error) {
      console.error("Clear all error:", error);
      this.showError("Network error. Please try again.");
    }
  }

  addClearAllButton() {
    const container = document.getElementById("recentDownloadsList");
    if (!container) return;

    // Remove existing clear all button if present
    const existingBtn = container.querySelector(".clear-all-container");
    if (existingBtn) {
      existingBtn.remove();
    }

    // Add clear all button at the bottom
    const clearAllBtn = document.createElement("div");
    clearAllBtn.className = "clear-all-container";
    clearAllBtn.innerHTML = `
        <button class="clear-all-btn" onclick="vidSparrow.clearAllDownloads()">
            <i class="fas fa-broom"></i> Clear All History
        </button>
    `;
    container.appendChild(clearAllBtn);
  }

  // Utility methods
  isValidUrl(string) {
    try {
      const url = new URL(string);
      return url.protocol === "http:" || url.protocol === "https:";
    } catch (_) {
      return false;
    }
  }

  formatDuration(seconds) {
    if (!seconds) return "Unknown";

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, "0")}:${secs
        .toString()
        .padStart(2, "0")}`;
    } else {
      return `${minutes}:${secs.toString().padStart(2, "0")}`;
    }
  }

  formatViews(count) {
    if (!count) return "Unknown";

    if (count >= 1000000) {
      return (count / 1000000).toFixed(1) + "M";
    } else if (count >= 1000) {
      return (count / 1000).toFixed(1) + "K";
    }
    return count.toString();
  }

  truncateText(text, maxLength) {
    if (!text) return "";
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  }

  // UI methods
  showLoading(message) {
    const previewBtn = document.getElementById("previewBtn");
    if (previewBtn) {
      previewBtn.disabled = true;
      previewBtn.innerHTML =
        '<i class="fas fa-spinner fa-spin"></i> Loading...';
    }
  }

  hideLoading() {
    const previewBtn = document.getElementById("previewBtn");
    if (previewBtn) {
      previewBtn.disabled = false;
      previewBtn.innerHTML = '<i class="fas fa-eye"></i> Preview';
    }
  }

  showProgress(message) {
    const progressContainer = document.getElementById("downloadProgress");
    const progressText = progressContainer?.querySelector(".progress-text");

    if (progressContainer && progressText) {
      progressText.textContent = message;
      progressContainer.classList.remove("hidden");
    }

    const downloadBtn = document.getElementById("downloadBtn");
    if (downloadBtn) {
      downloadBtn.disabled = true;
    }
  }

  updateProgress(message, percent) {
    const progressFill = document.querySelector(".progress-fill");
    const progressText = document.querySelector(".progress-text");

    if (progressFill) {
      progressFill.style.width = percent + "%";
    }
    if (progressText) {
      progressText.textContent = message;
    }
  }

  hideProgress() {
    const progressContainer = document.getElementById("downloadProgress");
    const progressFill = document.querySelector(".progress-fill");

    if (progressContainer) {
      progressContainer.classList.add("hidden");
    }
    if (progressFill) {
      progressFill.style.width = "0%";
    }

    const downloadBtn = document.getElementById("downloadBtn");
    if (downloadBtn) {
      downloadBtn.disabled = false;
    }
  }

  showError(message) {
    this.showToast(message, "error");
  }

  showToast(message, type = "info") {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll(".toast");
    existingToasts.forEach((toast) => toast.remove());

    // Create toast element
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
            <div class="toast-content">
                <i class="fas ${
                  type === "error" ? "fa-exclamation-circle" : "fa-info-circle"
                }"></i>
                <span>${message}</span>
            </div>
            <button class="toast-close">&times;</button>
        `;

    // Add styles
    toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${
              type === "error" ? "var(--error)" : "var(--secondary-dark)"
            };
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
            z-index: 10000;
            max-width: 400px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            animation: slideIn 0.3s ease;
            border: 1px solid ${
              type === "error" ? "var(--error)" : "var(--primary-cyan)"
            };
        `;

    // Close button
    const closeBtn = toast.querySelector(".toast-close");
    closeBtn.addEventListener("click", () => {
      toast.remove();
    });

    document.body.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
      if (toast.parentNode) {
        toast.remove();
      }
    }, 5000);
  }

  clearForm() {
    const urlInput = document.getElementById("videoUrl");
    if (urlInput) {
      urlInput.value = "";
    }
    this.clearPreview();
  }
}

// Add CSS for toast animations, delete buttons, and quality selector
const style = document.createElement("style");
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    .toast-close {
        background: none;
        border: none;
        color: white;
        font-size: 1.2rem;
        cursor: pointer;
        padding: 0;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: opacity 0.2s ease;
    }
    
    .toast-close:hover {
        opacity: 0.7;
    }
    
    .toast-content {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Quality Selector Styles */
    .quality-selector {
        margin: 20px 0;
        padding: 15px;
        background: var(--secondary-dark);
        border-radius: 8px;
        border: 1px solid var(--primary-cyan);
    }
    
    .quality-selector h4 {
        margin: 0 0 10px 0;
        color: var(--text-light);
        font-size: 16px;
        font-weight: 600;
    }
    
    .quality-options {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }
    
    .quality-option {
        padding: 8px 16px;
        background: var(--secondary);
        border: 2px solid var(--secondary);
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 14px;
        color: var(--text-light);
        font-weight: 500;
    }
    
    .quality-option:hover {
        border-color: var(--primary-cyan);
        background: var(--secondary-dark);
        transform: translateY(-2px);
    }
    
    .quality-option.selected {
        background: var(--primary-cyan);
        color: white;
        border-color: var(--primary-cyan);
    }
    
    .quality-option:disabled {
        background: var(--secondary);
        color: var(--text-muted);
        cursor: not-allowed;
        border-color: var(--secondary);
    }
    
    /* Delete button styles */
    .download-actions {
        display: flex;
        align-items: center;
        margin-left: auto;
        padding-left: 15px;
    }
    
    .delete-btn {
        background: var(--error);
        color: white;
        border: none;
        border-radius: 50%;
        width: 35px;
        height: 35px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
        opacity: 0.7;
    }
    
    .delete-btn:hover {
        opacity: 1;
        transform: scale(1.1);
        background: #d32f2f;
    }
    
    .clear-all-container {
        margin-top: 20px;
        text-align: center;
        padding-top: 20px;
        border-top: 1px solid var(--secondary-dark);
    }
    
    .clear-all-btn {
        background: linear-gradient(135deg, var(--error), #d32f2f);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 10px 20px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.3s ease;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    
    .clear-all-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(211, 47, 47, 0.4);
    }
    
    /* Update download item layout */
    .download-item {
        display: flex;
        align-items: center;
        background: var(--secondary-dark);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        transition: all 0.3s ease;
        border: 1px solid transparent;
    }
    
    .download-item:hover {
        border-color: var(--primary-cyan);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
    }
    
    .download-info {
        flex: 1;
        min-width: 0;
    }

    /* Responsive design for quality selector */
    @media (max-width: 768px) {
        .quality-options {
            flex-direction: column;
        }
        
        .quality-option {
            text-align: center;
        }
    }
`;
document.head.appendChild(style);

// Initialize the application when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM loaded, initializing VidSparrow...");
  window.vidSparrow = new VidSparrow();
});
