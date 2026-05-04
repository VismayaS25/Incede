function handleApply(){

    const user = localStorage.getItem("loggedInUser");

    if(!user){

    alert("Please login before applying.");

    window.location.href = "login.html";

    } else {

    window.location.href = "index.html";

    }

}
function logout(){

    localStorage.removeItem("loggedInUser");

    alert("Logged out successfully");

    window.location.href = "landing.html";

}
