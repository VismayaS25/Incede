document.getElementById("loginForm").addEventListener("submit", async function(e){

    e.preventDefault();

    const loginData = {
        email: document.getElementById("loginEmail").value,
        password: document.getElementById("loginPassword").value
    };

    try{

        const response = await fetch("http://127.0.0.1:8000/login",{
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify(loginData)
        });

        const result = await response.json();

        if(result.status === "success"){

            localStorage.setItem("loggedInUser", loginData.email);

            alert("Login successful");

            window.location.href = "index.html";

        }else{

            alert("Invalid email or password / Create an Account!!");

        }

    }catch(error){

        alert("Server not reachable");

    }

});