document.getElementById("signupForm").addEventListener("submit", async function(e){

    e.preventDefault();

    const userData = {

        name: document.getElementById("signupName").value,
        email: document.getElementById("signupEmail").value,
        password: document.getElementById("signupPassword").value
    };

    try{

        const response = await fetch("http://127.0.0.1:8000/signup",{

            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify(userData)

        });

        if(response.ok){

            alert("Account created successfully! Please login to apply.");

            window.location.href="login.html";

        }else{

            alert("Signup failed");

        }

    }catch(error){

        alert("Server not reachable");

    }

});