document.addEventListener("DOMContentLoaded", function(){

let formStartTime = Date.now();
let typingStart = null;
let typingEnd = null;


/* Typing Speed Tracking */

document.getElementById("name").addEventListener("keydown", () => {

    if(!typingStart){
        typingStart = Date.now();
    }

    typingEnd = Date.now();
});


/* Device Fingerprint */

function getDeviceFingerprint(){

    return (
        navigator.userAgent +
        navigator.language +
        screen.width +
        screen.height +
        navigator.hardwareConcurrency +
        navigator.platform +
        Intl.DateTimeFormat().resolvedOptions().timeZone
    );

}



/* Form Submit */

document.getElementById("applicationForm").addEventListener("submit", async function(e){

    e.preventDefault();

    const submitTime = Date.now();

    let typingSpeed = 0.0;

    if(typingStart && typingEnd){
        typingSpeed = (typingEnd - typingStart) / 1000;
    }

    const selectedRole = document.getElementById("job_role").value;
    const otherRole = document.getElementById("other_job_role").value;

    // Prevent empty other role
    if(selectedRole === "Other" && otherRole.trim() === ""){
        alert("Please enter your job role.");
        return;
    }

    const finalRole = selectedRole === "Other" ? otherRole : selectedRole;

    const behaviorData = {

        name: document.getElementById("name").value,
        email: document.getElementById("email").value,
        gender: document.getElementById("gender").value,
        phone: document.getElementById("phone").value,
        country: document.getElementById("country").value,

        job_role: finalRole,

        form_start_time: Math.floor(formStartTime/1000),
        form_submit_time: Math.floor(submitTime/1000),

        applications_today: 1,
        login_attempts: 1,
        device_fingerprint: getDeviceFingerprint(),
        session_duration: Math.floor((submitTime-formStartTime)/1000),

        account_age_days: 120,
        typing_speed: typingSpeed
    };

try{
    console.log("Sending data:", behaviorData);
    const response = await fetch("http://127.0.0.1:8000/fraud-check", {

        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify(behaviorData)

    });

    const result = await response.json();

    if(!response.ok){
        alert("Submission failed.");
        return;
    }

    if(result.status === "rejected"){
        alert(result.message);
        return;
    }

    alert("Application submitted successfully!");

    console.log("Redirecting to landing page...");

    setTimeout(() => {
        window.location.href = "landing.html";
    }, 1500);

}
catch(error){

    alert("Server not reachable.");
    console.error(error);

}

});

});

function checkOtherRole(){

    const roleSelect = document.getElementById("job_role");
    const otherInput = document.getElementById("other_job_role");

    if(roleSelect.value === "Other"){
        otherInput.style.display = "block";
    } else {
        otherInput.style.display = "none";
        otherInput.value = "";
    }
}
