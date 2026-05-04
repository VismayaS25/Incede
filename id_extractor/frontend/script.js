let selectedFile = null;

const fileInput = document.getElementById("fileInput");
const dropZone = document.getElementById("dropZone");
const previewImage = document.getElementById("previewImage");
const previewPDF = document.getElementById("previewPDF");


/* FILE INPUT CHANGE */

fileInput.addEventListener("change", function () {

    const file = this.files[0];

    if (!file) return;

    selectedFile = file;

    showPreview(file);

});


/* DROP ZONE CLICK */

dropZone.addEventListener("click", () => {
    fileInput.click();
});


/* DRAG OVER */

dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
});

/* DRAG LEAVE */

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
});


/* DROP FILE */

dropZone.addEventListener("drop", (e) => {

    e.preventDefault();
    dropZone.classList.remove("dragover");

    const file = e.dataTransfer.files[0];

    if (!file) return;

    selectedFile = file;

    showPreview(file);

});


/* PREVIEW FUNCTION */

function showPreview(file) {

    /* reset progress bar */

    document.getElementById("progressBar").style.width = "0%";
    document.getElementById("progressBarContainer").style.display = "none";

    previewImage.style.display = "none";
    previewPDF.style.display = "none";

    const url = URL.createObjectURL(file);

    if (file.type === "application/pdf") {

        previewPDF.src = url;
        previewPDF.style.display = "block";

    } else {

        previewImage.src = url;
        previewImage.style.display = "block";

    }

}



async function uploadFile() {


// const fileInput = document.getElementById("fileInput");
// const file = fileInput.files[0];

const file = selectedFile;

if (!file) {
    alert("Please select a document first.");
    return;
}

const loader = document.getElementById("loader");
loader.style.display = "block";

document.getElementById("progressBarContainer").style.display = "block";
document.getElementById("progressBar").style.width = "40%";

const formData = new FormData();
formData.append("file",file);

try {

    const response = await fetch("/extract-id", {
        method: "POST",
        body: formData
    });

    if (!response.ok) {
        throw new Error("Server error: " + response.status);
    }

    const result = await response.json();

    // if (!text) {
    //     throw new Error("Empty response from backend");
    // }

    // let result;

    // try {
    //     result = JSON.parse(text);
    // } catch (e) {
    //     console.error("Invalid JSON:", text);
    //     throw new Error("Server returned invalid response");
    // }

    

    document.getElementById("progressBar").style.width = "100%";

    loader.style.display = "none";

    // Show debug response
    document.getElementById("debugOutput").textContent =
        JSON.stringify(result, null, 2);

    console.log("API RESPONSE:", result);

    if (!result || result.status !== "success") {
        alert(result?.message || "Unsupported document");
        return;
    }

    const data = result.data || {};
    const docType = result.document_type || "";

    const aadhaarSection = document.getElementById("aadhaarSection");
    const panSection = document.getElementById("panSection");
    const dlSection = document.getElementById("dlSection");

    aadhaarSection.style.display = "none";
    panSection.style.display = "none";
    dlSection.style.display = "none";

    if (docType === "aadhaar") {

        aadhaarSection.style.display = "block";

        document.getElementById("name").value = data.name || "";
        document.getElementById("dob").value = data.dob || "";
        document.getElementById("gender").value = data.gender || "";
        document.getElementById("aadhaar").value = data.aadhaar_number || "";
        document.getElementById("address").value = data.address || "";
    }

    else if (docType === "pan") {

        panSection.style.display = "block";

        document.getElementById("pan_name").value = data.name || "";
        document.getElementById("pan_dob").value = data.dob || "";
        document.getElementById("pan_number").value = data.pan_number || "";
        document.getElementById("father_name").value = data.father_name || "";
    }

    else if(docType === "driving_license"){

    // document.getElementById("dlSection").style.display="block"
    dlSection.style.display = "block";

    document.getElementById("dl_name").value=data.name || ""
    document.getElementById("dl_dob").value=data.dob || ""
    document.getElementById("dl_number").value=data.dl_number || ""
    document.getElementById("permanent_address").value=data.permanent_address || ""
    document.getElementById("present_address").value=data.present_address || ""
    document.getElementById("pincode").value=data.pincode || ""

    }

} catch (error) {

    loader.style.display = "none";

    console.error("FRONTEND ERROR:", error);

    document.getElementById("debugOutput").textContent =
        "Frontend Error: " + error.message;

    alert("Frontend error occurred. Check console.");

}


}



