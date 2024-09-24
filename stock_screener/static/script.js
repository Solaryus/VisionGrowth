document.addEventListener('DOMContentLoaded', function() {
    // Charger les principaux stocks
    fetch('/get_main_stocks')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('stocks-table-body');
            tableBody.innerHTML = '';
            data.forEach(stock => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${stock.name}</td>
                    <td>${stock.price}</td>
                    <td>${stock.change}</td>
                    <td>${stock.volume}</td>
                `;
                tableBody.appendChild(row);
            });
        });

    // Rechercher un stock
    document.getElementById('search-button').addEventListener('click', function() {
        const searchBar = document.getElementById('search-bar');
        const stockSymbol = searchBar.value.trim();

        if (stockSymbol) {
            fetch('/search_stock', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ symbol: stockSymbol })
            })
            .then(response => response.json())
            .then(data => {
                const tableBody = document.getElementById('search-results-body');
                tableBody.innerHTML = '';
                if (data.error) {
                    alert(data.error);
                } else {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${data.name}</td>
                        <td>${data.price}</td>
                        <td>${data.change}</td>
                        <td>${data.volume}</td>
                    `;
                    tableBody.appendChild(row);
                }
            })
            .catch(error => console.error('Erreur:', error));
        }
    });
});
