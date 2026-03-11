function signup() {
    const user = {
        name: document.getElementById("name").value,
        email: document.getElementById("email").value,
        phone: document.getElementById("phone").value,
        location: document.getElementById("location").value,
        password: document.getElementById("password").value
    };

    if (!user.email || !user.password) {
        alert("Please fill all required fields");
        return;
    }

    localStorage.setItem("userData", JSON.stringify(user));
    alert("Signup successful!");
    window.location.href = "login.html";
    window.location.href = "login_krishak.html";
}

function login() {
    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;

    const storedUser = JSON.parse(localStorage.getItem("userData"));

    if (storedUser && email === storedUser.email && password === storedUser.password) {
        alert("Login successful!");
        window.location.href = "krishak_frontend.html";
    } else {
        alert("Invalid email or password");
    }
}
