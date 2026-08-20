document.addEventListener("DOMContentLoaded", () => {
    const cameraInput = document.getElementById("camera-input");
    const galleryInput = document.getElementById("gallery-input");
    
    const heroSection = document.getElementById("hero-section");
    const previewSection = document.getElementById("preview-section");
    const resultSection = document.getElementById("result-section");
    
    const imagePreview = document.getElementById("image-preview");
    const btnCancel = document.getElementById("btn-cancel");
    const btnAnalyze = document.getElementById("btn-analyze");
    const btnCloseResult = document.getElementById("btn-close-result");
    const loadingOverlay = document.getElementById("loading-overlay");
    const toast = document.getElementById("toast");
    const toastMessage = document.getElementById("toast-message");

    let currentBase64 = null;

    // Handle file selection (Camera or Gallery)
    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Ensure it's an image
        if (!file.type.startsWith("image/")) {
            showToast("Por favor, selecione uma imagem válida.");
            return;
        }

        const reader = new FileReader();
        reader.onload = (event) => {
            currentBase64 = event.target.result;
            imagePreview.src = currentBase64;
            
            // Switch UI states
            heroSection.classList.add("hidden");
            resultSection.classList.add("hidden");
            previewSection.classList.remove("hidden");
        };
        reader.onerror = () => {
            showToast("Erro ao ler o arquivo.");
        };
        reader.readAsDataURL(file);
    };

    cameraInput.addEventListener("change", handleFileSelect);
    galleryInput.addEventListener("change", handleFileSelect);

    // Cancel analysis
    btnCancel.addEventListener("click", () => {
        resetUI();
    });

    // Close result
    btnCloseResult.addEventListener("click", () => {
        resetUI();
    });

    // Analyze Image
    btnAnalyze.addEventListener("click", async () => {
        if (!currentBase64) return;

        // Show loading state
        btnAnalyze.disabled = true;
        btnCancel.disabled = true;
        loadingOverlay.classList.remove("hidden");

        try {
            const response = await fetch("/api/predict", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ image_b64: currentBase64 })
            });

            const data = await response.json();

            if (data.status === "success") {
                displayResult(data.prediction);
            } else {
                showToast(data.message || "Erro durante a análise.");
                resetLoadingState();
            }
        } catch (error) {
            console.error(error);
            showToast("Erro de rede ao conectar com o servidor.");
            resetLoadingState();
        }
    });

    function displayResult(prediction) {
        // Hide preview actions, show result
        previewSection.classList.add("hidden");
        resultSection.classList.remove("hidden");
        resetLoadingState();

        // Populate Main Class
        document.getElementById("res-class").textContent = prediction.class;
        const mainConf = prediction.confidence;
        document.getElementById("res-class-conf").textContent = `${mainConf}%`;
        
        // Populate Subtype
        document.getElementById("res-sub-class").textContent = prediction.subtype_class;
        const subConf = prediction.subtype_confidence;
        document.getElementById("res-sub-conf").textContent = `${subConf}%`;

        // Animate Progress Bars
        setTimeout(() => {
            document.getElementById("res-class-conf-bar").style.width = `${mainConf}%`;
            document.getElementById("res-sub-conf-bar").style.width = `${subConf}%`;
        }, 100);
    }

    function resetUI() {
        currentBase64 = null;
        imagePreview.src = "";
        cameraInput.value = "";
        galleryInput.value = "";
        
        previewSection.classList.add("hidden");
        resultSection.classList.add("hidden");
        heroSection.classList.remove("hidden");
        
        // Reset bars
        document.getElementById("res-class-conf-bar").style.width = "0%";
        document.getElementById("res-sub-conf-bar").style.width = "0%";
    }

    function resetLoadingState() {
        btnAnalyze.disabled = false;
        btnCancel.disabled = false;
        loadingOverlay.classList.add("hidden");
    }

    function showToast(message) {
        toastMessage.textContent = message;
        toast.classList.remove("hidden");
        setTimeout(() => {
            toast.classList.add("hidden");
        }, 3000);
    }
});
