import Dexie, { type Table } from 'dexie';
export type StoredSnapshot = { id:string; createdAt:number; generatedImage:string; prompt:string; note:string; importedImage?:string; humanDrawLayer?:[number,number][]; guideEraseMask?:string; guideComposite?:string; lastNoiseMask?:[number,number][]; diffusionStepCount?:number; seed?:number };
class SnapshotDatabase extends Dexie { snapshots!: Table<StoredSnapshot,string>; constructor(){super('live-diffusion-canvas');this.version(1).stores({snapshots:'id,createdAt'});} }
export const snapshotDb = new SnapshotDatabase();
export const loadSnapshots = () => snapshotDb.snapshots.orderBy('createdAt').toArray();
export const persistSnapshot = (snapshot:StoredSnapshot) => snapshotDb.snapshots.put(snapshot);
export const clearSnapshots = () => snapshotDb.snapshots.clear();
