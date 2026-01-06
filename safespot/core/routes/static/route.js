// Carte interactive pour choisir la destination
document.addEventListener('DOMContentLoaded', function () {
	var mapDiv = document.getElementById('map');
	if (!mapDiv) return;

	var map = L.map('map').setView([36.8, 10.2], 8); // Centré sur la Tunisie par défaut
	L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
		maxZoom: 18,
		attribution: '© OpenStreetMap contributors'
	}).addTo(map);

	var marker;
	map.on('click', function (e) {
		var lat = e.latlng.lat.toFixed(5);
		var lon = e.latlng.lng.toFixed(5);
		document.getElementById('lat').value = lat;
		document.getElementById('lon').value = lon;
		if (marker) {
			marker.setLatLng(e.latlng);
		} else {
			marker = L.marker(e.latlng).addTo(map);
		}
	});
});
