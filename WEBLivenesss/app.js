const video = document.getElementById("video");       //Live Webcam connection
video.setAttribute("autoplay", true);
video.setAttribute("playsinline", true);
video.muted = true;
const canvas = document.getElementById("output");     //FaceMesh landmarks
const ctx = canvas.getContext("2d");
const startBtn = document.getElementById("startBtn"); //Button
const timerOverlay = document.getElementById("challengeTimer");  //Timer for challenge 
let camera = null;
let stopTimeout = null;

      //BLINK VARIABLES
// let blinkDetected = false;
let blinkCount = 0;
let earThreshold = 0.25;                             //EyeAspectRatio(determines open/close)
let earConsecutiveFrames = 0;
let EAR_FRAME_LIMIT = 2;                            //valid only if closed for ≥2 frames 

//EYEBROW VARIABLES
let eyebrowRaised = false;
let eyebrowBaseline = null;
let eyebrowThreshold = 0.015;                      
let eyebrowFrameCount = 0;

//HEAD MOVEMENT VARIABLES
let headMoved = false;                             //Detects head movement
let noseBaseline = null;
let headThreshold = 0.03;   
let noseFrameCount = 0;

let lastVideoFrame = null;                        //Captures verified image
let capturedFrames = [];
const MAX_FRAMES = 16;
let frameInterval = null;
let lastCaptureTime = 0;

const CAPTURE_INTERVAL = 150;                     //Trying to capturing 16 frames in 5sec
let captureTimer = null;
let humanDetected = false;
let faceMeshEnabled = false;
let faceLostFrames = 0;

const FACE_LOST_LIMIT = 5; // 150ms
let noHumanTimer = null;
let poseStableFrames = 0;

const POSE_STABLE_REQUIRED = 3;
let systemBlocked = false;
let occlusionFailCount = 0;
const OCCLUSION_FAIL_LIMIT = 1;

//FACE DETECTION MODEL
const faceDetection = new FaceDetection({
    locateFile: (file) =>
        `https://cdn.jsdelivr.net/npm/@mediapipe/face_detection/${file}`,
});

faceDetection.setOptions({
    model: "short",          // FAST & STRICT
    minDetectionConfidence: 0.8, // IMPORTANT
});

faceDetection.onResults(onFaceDetectionResults);

//RANDOM CHALLENGE
const CHALLENGES = ["BLINK_TWICE", "RAISE_EYEBROWS"];
let currentChallenge = null;                       //Stores
let challengeStartTime = null;                     //Timer
let challengePassed = false;
let captureEnabled = false;
const TOTAL_VERIFICATION_TIME = 8000; // 8 sec total
const CHALLENGE_TIME = 4000;          // first half
const CAPTURE_TIME = 2500;            // second half

//Timer (Countdown)
let preChallengeCountdown = 3;
let countdownInterval = null;
let challengeActive = false;

//Face Mesh
const faceMesh = new FaceMesh({
    locateFile: (file) =>
        `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`,
});

faceMesh.setOptions({
    maxNumFaces: 1,                              //Allows only 1 face
    refineLandmarks: true,
    minDetectionConfidence: 0.5,  
    minTrackingConfidence: 0.5,                 //landmarking = conf threshold 
});
faceMesh.onResults(onResults);

//Start Button
startBtn.addEventListener("click", () => {

    poseStableFrames = 0;

    captureEnabled = false;
    challengeStartTime = null;
    capturedFrames = [];

    // blinkDetected = false;
    earConsecutiveFrames = 0;
    blinkCount = 0;
    eyebrowRaised = false;
    eyebrowBaseline = null;
    eyebrowFrameCount = 0;
    headMoved = false;
    noseBaseline = null;
    noseFrameCount = 0;
    challengePassed = false;
    window.occlusionChecked = false;
    challengeActive = false;
    systemBlocked = false;
    occlusionFailCount = 0;

    //RANDOM CHALLENGE
    currentChallenge = CHALLENGES[Math.floor(Math.random() * CHALLENGES.length)];   //Gives random challenges

    alert(`CHALLENGE: ${formatChallenge(currentChallenge)}`);                      //instruction

    startBtn.disabled = true;
    startCamera();
});

//Start Camera 
async function startCamera() {
    humanDetected = false;
    faceMeshEnabled = false;
    capturedFrames = [];

    camera = new Camera(video, {
        onFrame: async () => {
            await faceDetection.send({ image: video });

            if (faceMeshEnabled) {
                await faceMesh.send({ image: video });
            }
        },
        width: 640,
        height: 480,
    });

    await camera.start(); 

    // Auto-close camera if no human detected in 1.5 sec
    noHumanTimer = setTimeout(() => {
    
        if (!humanDetected && camera) {
            alert(" No Human Face Detected ! :< ");

            //  STOP CAMERA EVEN IF NO HUMAN
            camera.stop();
            camera = null;
            clearInterval(captureTimer);
            captureTimer = null;
            startBtn.disabled = false;
        }
    }, 3000);

    // FRAME CAPTURE TIMER
    captureTimer = setInterval(() => {
        if (!humanDetected) return;
        if (!captureEnabled) return;                           //Frames captured ONLY after challenge success
        if (capturedFrames.length >= MAX_FRAMES) return;       //Stops @16 frames
        if (video.videoWidth === 0 || video.videoHeight === 0) return;

        const tempCanvas = document.createElement("canvas");
        tempCanvas.width = video.videoWidth;
        tempCanvas.height = video.videoHeight;

        const ctx = tempCanvas.getContext("2d");
        ctx.drawImage(video, 0, 0);

        capturedFrames.push(tempCanvas.toDataURL("image/jpeg"));      //read to Captures and upload at backend
        console.log("Captured frame:", capturedFrames.length);
    }, CAPTURE_INTERVAL);
}

// FACE DETECTION 
function onFaceDetectionResults(results) {
    if (!results.detections || results.detections.length === 0) {
        faceLostFrames++;

        if (faceLostFrames < FACE_LOST_LIMIT) {
            return;  // tolerate brief loss
        }

        humanDetected = false;
        faceMeshEnabled = false;

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = "red";
        ctx.font = "22px Arial";
        ctx.fillText(" ", 20, 40)
        return;
    }

    //  REAL HUMAN FACE DETECTED
    faceLostFrames = 0;
    humanDetected = true;
    faceMeshEnabled = true;

    if (!window.occlusionChecked) {
        window.occlusionChecked = true;
        checkOcclusionFrame();
    }

    //  CANCEL NO-HUMAN TIMER
    if (noHumanTimer) {
        clearTimeout(noHumanTimer);
        noHumanTimer = null;
    }
}

// To Check background [lighting]
function checkLighting(canvas) {
    const ctx = canvas.getContext("2d");
    const frame = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = frame.data;
    let brightness = 0;
    let darkPixels = 0;
    let brightPixels = 0;

    for (let i = 0; i < data.length; i += 4) {
        const r = data[i];
        const g = data[i+1];
        const b = data[i+2];
        const avg = (r + g + b) / 3;
        brightness += avg;
        if (avg < 40) darkPixels++;
        if (avg > 220) brightPixels++;
    }

    brightness /= (data.length / 4);

    const darkRatio = darkPixels / (data.length / 4);
    const brightRatio = brightPixels / (data.length / 4);

    //  LOW LIGHT
    if (brightness < 85 || darkRatio > 0.5) {
        return "LOW_LIGHT";
    }

    // BACKLIGHT (window behind)
    if (brightRatio > 0.18 && brightness > 120) {
        return "BACKLIGHT";
    }

    return "OK";
}

// Occlusion Checking (Checks face is covered or not )
async function checkOcclusionFrame() {
    if (!video.videoWidth) return;
    if (systemBlocked) return;

    const tempCanvas = document.createElement("canvas");
    tempCanvas.width = video.videoWidth;
    tempCanvas.height = video.videoHeight;
    const ctx = tempCanvas.getContext("2d");
    ctx.drawImage(video,0,0);
    const lightingResult = checkLighting(tempCanvas);     // LIGHTING CHECK

    if (lightingResult === "LOW_LIGHT") {
        alert("Environment too dark. Please move to better lighting.");
        stopCamera();
        return;
    }

    if (lightingResult === "BACKLIGHT") {
        alert("Backlight detected. Do not stand in front of window/light source.");
        stopCamera();
        return;
    }

    const blob = await new Promise(res =>
        tempCanvas.toBlob(res,"image/jpeg")
    );

    const formData = new FormData();
    formData.append("file", blob, "frame.jpg");

    const response = await fetch("http://127.0.0.1:8000/check_occlusion", {
        method:"POST",
        body: formData
    });

    const data = await response.json();

    if (data.status === "covered") {
        occlusionFailCount++;

        console.log("Occlusion fail:", occlusionFailCount, data.reason);

        if (occlusionFailCount >= OCCLUSION_FAIL_LIMIT) {
            systemBlocked = true;        //  stop everything
            faceMeshEnabled = false;     //  disable mesh
            alert("Face covered: " + data.reason);
            stopCamera();
            return;
        }

        // wait for next frame instead of rejecting
        setTimeout(checkOcclusionFrame, 300);
        return;
    }

    // If Occlusion Passed --  Challenge Timer Starts
    if (challengeStartTime === null) {
        startPreChallengeCountdown();
    }
}

//Challenge Timer Countdown
function startPreChallengeCountdown() {
    preChallengeCountdown = 3;
    challengeActive = false;
    timerOverlay.style.display = "block";
    countdownInterval = setInterval(() => {
        timerOverlay.innerText = `Starting in ${preChallengeCountdown}`;
        preChallengeCountdown--;

        if (preChallengeCountdown < 0) {
            clearInterval(countdownInterval);
            timerOverlay.innerText = "GO!";
            setTimeout(()=>{
                timerOverlay.style.display = "none";
            },700);
            challengeStartTime = Date.now();
            challengeActive = true;
            stopTimeout = setTimeout(() => {
                stopCamera();
            }, TOTAL_VERIFICATION_TIME);
            console.log("Challenge officially started");
        }
    }, 1000);
}

//Capture the image from the video
function captureFrameFromVideo() {
    const captureCanvas = document.getElementById("captureCanvas");
    const captureCtx = captureCanvas.getContext("2d");
    captureCanvas.width = video.videoWidth;
    captureCanvas.height = video.videoHeight;
    captureCtx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);

    return captureCanvas.toDataURL("image/png");
}

// Display Friendly Challenge Text
function formatChallenge(challenge) {
    switch (challenge) {
        case "BLINK_TWICE":
            return "Blink your eyes twice";
        case "TURN_HEAD_LEFT":
            return "Turn your head to the LEFT";
        case "RAISE_EYEBROWS":
            return "Raise your eyebrows";
        default:
            return "";
    }
}

//Stop Camera
async function stopCamera() {
    if (!camera) {
        console.warn("stopCamera called twice — ignored");   
        return;
    }

    clearTimeout(stopTimeout);        // Ignores if the camera is called a multiple of times to prevent crashing
    stopTimeout = null;

    if (!humanDetected) {
        alert("No human face detected :( ");
        return;
    }

    //CAPTUREs IMAGE WHILE VIDEO IS STILL LIVE
    const verifiedImageDataURL = captureFrameFromVideo();
    camera.stop();
    camera = null;
    clearInterval(captureTimer);    // Stops frame capturing
    captureTimer = null;
    startBtn.disabled = false;
    console.log("Total frames captured:", capturedFrames.length);
                   
    if (!challengePassed) {
        alert("Challenge not completed in time");
        // camera.stop();
        // camera = null;
        return;
    }

    if (capturedFrames.length < MAX_FRAMES) {
        alert("Not enough frames captured. Please try again later!! ");
        return;
    }
    // if frames captured correctly calls /verify API
    console.log("Sending frames to backend:", capturedFrames.length);

    let result;
    try {
        result = await sendFramesToBackend();
    } catch (err) {
        alert("Error: " + err.message);
        console.error(err);
        return;
    }

    if (result.prediction === "LIVE" && result.live_score > 0.7) {
        alert(`LIVE VERIFIED (Score: ${result.live_score})`);
        captureVerifiedImage(verifiedImageDataURL);
    } else {
        alert(`Prediction: ${result.prediction}\nScore: ${result.live_score}`)
    }
}

// Backend function
async function sendFramesToBackend() {
    const formData = new FormData();

    capturedFrames.forEach((frame, index) => {
        const blob = dataURLtoBlob(frame);
        formData.append("files", blob, `frame_${index}.jpg`);
    });    //Sends the cpatured frames to API

    const response = await fetch("http://127.0.0.1:8000/verify", {
        method: "POST",
        body: formData,
    });              //Post request to backend

    const text = await response.text();
    console.log("Raw backend response:", text);

    if (!response.ok) {
        throw new Error(text || "Backend verification failed");
    }

    return JSON.parse(text);
}

//Blob (Converts Baseimage to binary blob)
function dataURLtoBlob(dataURL) {
    const arr = dataURL.split(",");
    const mime = arr[0].match(/:(.*?);/)[1];
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);

    while (n--) {
        u8arr[n] = bstr.charCodeAt(n);
    }

    return new Blob([u8arr], { type: mime });
}

//EAR CALCULATION
function distance(p1, p2) {
    return Math.hypot(p1.x - p2.x, p1.y - p2.y);
}

function calculateEAR(landmarks) {
    if (
        !landmarks ||
        !landmarks[159] ||
        !landmarks[145] ||
        !landmarks[33] ||
        !landmarks[133]
    ) {
        return 1.0;        //safe default (eyes open)
    }
    //Eye landmark
    const upper = landmarks[159];
    const lower = landmarks[145];
    const left = landmarks[33];
    const right = landmarks[133];

    return distance(upper, lower) / distance(left, right);
}

function calculateEyebrowDistance(landmarks) {
    if (
        !landmarks ||
        !landmarks[70] ||
        !landmarks[159]
    ) {
        return 0;      //SAFE DEFAULT
    }

    const eyebrow = landmarks[70];
    const eyeUpper = landmarks[159];
    return Math.abs(eyebrow.y - eyeUpper.y);
}

//half face and lightings
function globalEnvironmentCheck(landmarks, canvasFrame) {

    // if (systemBlocked) return ;
    if (systemBlocked) return false;

    //  POSE CHECK 
    const leftEye = landmarks[33];
    const rightEye = landmarks[263];
    const nose = landmarks[1];
    const eyeTilt = Math.abs(leftEye.y - rightEye.y);
    const center = (leftEye.x + rightEye.x) / 2;
    const noseOffset = Math.abs(nose.x - center);
    const eyeToNose = Math.abs((leftEye.y + rightEye.y)/2 - nose.y);

    //  HALF FACE / SIDE FACE / TILT
    if (noseOffset > 0.045 || eyeTilt > 0.04 || eyeToNose < 0.05) {
        systemBlocked = true;
        alert("Face not straight. Look directly at camera.");
        stopCamera();
        return false;
    }

    // LIGHTING CHECK 
    const lighting = checkLighting(canvasFrame);

    if (lighting === "LOW_LIGHT") {
        systemBlocked = true;
        alert("Too dark. Increase lighting.");
        stopCamera();
        return false;
    }

    if (lighting === "BACKLIGHT") {
        systemBlocked = true;
        alert("Backlight detected. Face light should be in front.");
        stopCamera();
        return false;
    }
    return true;
}

//to check mouth visiblity
function mouthVisibleCheck(landmarks) {
    const left = landmarks[61];
    const right = landmarks[291];
    const top = landmarks[13];
    const bottom = landmarks[14];
    const chin = landmarks[152];

    if (!left || !right || !top || !bottom || !chin) {
        return false;
    }

    // Check if mouth area is inside frame
    const points = [left, right, top, bottom, chin];

    for (let p of points) {
        if (p.x < 0.05 || p.x > 0.95) return false;
        if (p.y < 0.05 || p.y > 0.95) return false;
    }

    // width check (only reject if extremely small)
    const width = Math.abs(left.x - right.x);
    if (width < 0.01) return false;
    return true;
}

// On Results
function onResults(results) {
    // if (systemBlocked) return;
    if (systemBlocked) {
        ctx.clearRect(0,0,canvas.width,canvas.height);
        return;
    }

    if (!humanDetected) {
        return; 
    }
    
    if (
        !results.multiFaceLandmarks ||
        results.multiFaceLandmarks.length === 0
    ) return;

    const landmarks = results.multiFaceLandmarks[0];      //Single Face
    
    //Checks mouth visiblity and rejects
    if (!mouthVisibleCheck(landmarks)) {
        systemBlocked = true;
        alert("CLEAR FACE IS NOT FULLY VISIBLE");
        stopCamera();
        return;
    }

    // Creating temp canvas for lighting check
    const tempCanvas = document.createElement("canvas");
    tempCanvas.width = video.videoWidth;
    tempCanvas.height = video.videoHeight;
    const tctx = tempCanvas.getContext("2d");
    tctx.drawImage(video, 0, 0);

    // GLOBAL BLOCK (runs always)
    if (!globalEnvironmentCheck(landmarks, tempCanvas)) {
        return;
    }
  
    // POSE CONTROL
    const leftEye = landmarks[33];
    const rightEye = landmarks[263];
    const nose = landmarks[1];
    const eyeTilt = Math.abs(leftEye.y - rightEye.y);
    const center = (leftEye.x + rightEye.x) / 2;
    const noseOffset = Math.abs(nose.x - center);
    const eyeToNose = Math.abs((leftEye.y + rightEye.y)/2 - nose.y);

    // ONLY AFTER CHALLENGE PASSED
    if (challengePassed) {

        // STRICT 
        const badPose =
            noseOffset > 0.045 ||   // side face
            eyeTilt > 0.035 ||      // tilt
            eyeToNose < 0.05;       // looking down

        if (badPose) {
            console.log(" BAD POSE DURING CAPTURE");
            alert(" Keep face straight ");
            stopCamera();
            return;
        }

        // Require stable frames before capture
        if (!captureEnabled) {
            poseStableFrames++;
            if (poseStableFrames >= POSE_STABLE_REQUIRED) {
                captureEnabled = true;
                console.log("POSE LOCKED → capture started");
            }
        }
    }

    if (!landmarks || landmarks.length < 468) {
        return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(results.image, 0, 0, canvas.width, canvas.height);

        //Stores last valid video frame for capture
        lastVideoFrame = results.image;

        //Draws mesh
        drawConnectors(ctx, landmarks, FACEMESH_TESSELATION,
            { color: "#00ff99", lineWidth: 1 });

        //BLINK LOGIC
        const ear = calculateEAR(landmarks);

        if (ear < earThreshold) {
            earConsecutiveFrames++;
        } else {
            if (earConsecutiveFrames >= EAR_FRAME_LIMIT) {
                blinkCount++;
                console.log("Blink count:", blinkCount);
            }
            earConsecutiveFrames = 0;
        }

        // Display EAR
        ctx.fillStyle = "red";
        ctx.font = "18px Arial";
        ctx.fillText(`EAR: ${ear.toFixed(2)}`, 20, 30);

        //EYEBROW LOGIC
        const eyebrowDist = calculateEyebrowDistance(landmarks);
        //EYEBROW BASELINE STABILIZATION
        if (eyebrowBaseline === null) {
            eyebrowBaseline = eyebrowDist;
            eyebrowFrameCount = 1;
        } else if (eyebrowFrameCount < 10) {
            eyebrowBaseline =
                (eyebrowBaseline * eyebrowFrameCount + eyebrowDist) /
                (eyebrowFrameCount + 1);
            eyebrowFrameCount++;
        }

        //EYEBROW RAISE CHECK
        if (eyebrowDist - eyebrowBaseline > eyebrowThreshold) {
            eyebrowRaised = true;
        }

        // Display eyebrow info
        ctx.fillStyle = "yellow";
        ctx.fillText(`Eyebrow Δ: ${(eyebrowDist - eyebrowBaseline).toFixed(3)}`, 20, 60);

        //HEAD MOVEMENT LOGIC
        // const noseX = landmarks[1].x;
        if (!landmarks[1]) return;
        const noseX = landmarks[1].x;

        // Baseline stabilization (first ~10 frames)
        if (noseBaseline === null) {
            noseBaseline = noseX;
            noseFrameCount = 1;
        } else if (noseFrameCount < 10) {
            noseBaseline =
                (noseBaseline * noseFrameCount + noseX) /
                (noseFrameCount + 1);
            noseFrameCount++;
        }

        // Check head movement (left/right)
        if (Math.abs(noseX - noseBaseline) > headThreshold) {
            headMoved = true;
        }

        // Display head movement info
        ctx.fillStyle = "cyan";
        ctx.fillText(
            `Head ΔX: ${(noseX - noseBaseline).toFixed(3)}`,
            20,
            90
        );

        //CHALLENGE VALIDATION

        if (!challengePassed && challengeActive) {
            const now = Date.now();

            //TIMEOUT → FAIL
            if (Date.now() - challengeStartTime > CHALLENGE_TIME && !challengePassed) {
                alert("Challenge failed :( ");
                stopCamera();
                return;
            }

            // CHECK CHALLENGE           
            if (currentChallenge === "BLINK_TWICE" && blinkCount >= 2 && !challengePassed) {
                challengePassed = true;
                blinkCount = 0;
                headMoved = false;        
                eyebrowRaised = false;
                
                console.log("Challenge BLINK_TWICE passed → capture started");
            }

            if (currentChallenge === "RAISE_EYEBROWS" && eyebrowRaised && !challengePassed) {
                challengePassed = true;
                // captureEnabled = true;
                blinkCount = 0;
                headMoved = false;       
                eyebrowRaised = false;
                console.log("Challenge RAISE_EYEBROWS passed → capture started");
            }
        }
}

function captureVerifiedImage(imageDataURL) {
    const link = document.createElement("a");
    link.href = imageDataURL;
    link.download = "verified_live_image.png";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    console.log("Verified live image captured successfully");
}

