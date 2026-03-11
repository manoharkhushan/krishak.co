// Handle signup form submission
document.getElementById('signupForm')?.addEventListener('submit', function(e) {
    e.preventDefault();

    const formData = new FormData(this);

    fetch('/signup', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const messageDiv = document.getElementById('message');
        if (data.success) {
            messageDiv.className = 'message success';
            messageDiv.textContent = data.message;
            messageDiv.style.display = 'block';
            // Redirect to home after successful signup (auto-login)
            setTimeout(() => {
                window.location.href = data.redirect || '/home';
            }, 1500);
        } else {
            messageDiv.className = 'message error';
            messageDiv.textContent = data.message;
            messageDiv.style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const messageDiv = document.getElementById('message');
        messageDiv.className = 'message error';
        messageDiv.textContent = 'An error occurred. Please try again.';
        messageDiv.style.display = 'block';
    });
});

// Handle login form submission
document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const data = Object.fromEntries(formData);

    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        const messageDiv = document.getElementById('message');
        if (data.success) {
            messageDiv.className = 'message success';
            messageDiv.textContent = data.message;
            messageDiv.style.display = 'block';
            // Redirect to home after successful login
            setTimeout(() => {
                window.location.href = data.redirect || '/home';
            }, 1000);
        } else {
            messageDiv.className = 'message error';
            messageDiv.textContent = data.message;
            messageDiv.style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const messageDiv = document.getElementById('message');
        messageDiv.className = 'message error';
        messageDiv.textContent = 'An error occurred. Please try again.';
        messageDiv.style.display = 'block';
    });
});

// Handle expense form submission
document.getElementById('expenseForm')?.addEventListener('submit', function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const data = Object.fromEntries(formData);

    fetch('/api/expenses', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Expense added successfully!');
            location.reload(); // Refresh to show new expense
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    });
});

// Function to delete expense
function deleteExpense(expenseId) {
    if (confirm('Are you sure you want to delete this expense?')) {
        fetch('/api/expenses', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ expense_id: parseInt(expenseId) })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Expense deleted successfully!');
                location.reload(); // Refresh to update the list
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    }
}

// Load category chart on profile page
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('categoryChart')) {
        fetch('/api/analytics')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const ctx = document.getElementById('categoryChart').getContext('2d');
                new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: data.category_breakdown.map(item => item.category_name),
                        datasets: [{
                            data: data.category_breakdown.map(item => item.total_amount),
                            backgroundColor: [
                                '#0984e3', '#00b894', '#e17055', '#fdcb6e', '#6c5ce7',
                                '#a29bfe', '#fd79a8', '#e84393', '#00cec9', '#55efc4'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'bottom',
                            }
                        }
                    }
                });
            }
        })
        .catch(error => console.error('Error loading analytics:', error));
    }
});
