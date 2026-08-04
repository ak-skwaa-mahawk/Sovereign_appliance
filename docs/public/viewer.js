document.getElementById("loadLedger").onclick = async () => {
  const res = await fetch("/ledger");
  const data = await res.json();
  document.getElementById("ledgerOutput").textContent =
    JSON.stringify(data, null, 2);
};