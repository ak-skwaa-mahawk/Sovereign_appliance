/*
 * Registry discovery client for Sovereign Coil
 * Starts with North Star seed and follows soliton-seeds.json
 */

export interface SolitonSeedNode {
  name: string;
  designation: string;
  location: string;
  http: string;
  ws?: string;
  codex: string;
  kernel: string;
  nds_certified: boolean;
}

export async function discoverRegistryNodes(): Promise<SolitonSeedNode[]> {
  try {
    const res = await fetch("https://northstar.soliton.registry/.well-known/soliton-seeds.json");
    if (!res.ok) throw new Error("Failed to fetch seeds");
    const json = await res.json();
    return json.nodes as SolitonSeedNode[];
  } catch (e) {
    console.warn("Registry discovery failed, using fallback North Star", e);
    return [
      {
        name: "North Star Seed Node",
        designation: "Nᵒᵣᵗʰ-001",
        location: "Alaska",
        http: "https://northstar.soliton.registry",
        ws: "wss://northstar.soliton.registry:4001",
        codex: "Codex.Legis.Neurodata.v1",
        kernel: "Ił7",
        nds_certified: true
      }
    ];
  }
}

import { discoverRegistryNodes } from "./registryDiscovery";

let cachedBaseUrl: string | null = null;

async function getBaseUrl(): Promise<string> {
  if (cachedBaseUrl) return cachedBaseUrl;
  const nodes = await discoverRegistryNodes();
  // naive: take first certified node
  const node = nodes.find(n => n.nds_certified) || nodes[0];
  cachedBaseUrl = node.http.replace(/\/$/, "");
  return cachedBaseUrl!;
}

export async function logAggregateRemote(packet: any) {
  const base = await getBaseUrl();
  await fetch(`${base}/aggregate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(packet)
  });
}

export async function logRevocationRemote(receipt: any) {
  const base = await getBaseUrl();
  await fetch(`${base}/revoke`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(receipt)
  });
}