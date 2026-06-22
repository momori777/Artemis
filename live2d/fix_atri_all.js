const fs = require('fs');
const path = require('path');
const modelDir = path.join(__dirname, 'model', 'atri');
const modelJson = path.join(modelDir, 'atri.model3.json');
const j = JSON.parse(fs.readFileSync(modelJson, 'utf8'));
const m = j.FileReferences.Motions;

// Fix hair
if (m.hair) {
  m.hair.forEach((it, i) => {
    it.Name = `Hair_${i}`;
  });
  console.log('Fixed hair:', m.hair.length, 'items');
}

// Fix face - note face_0 was pointing to Motions_hair_0, fix to Motions_face_0
if (m.face) {
  m.face.forEach((it, i) => {
    it.Name = `Face_${i}`;
    it.File = `Motions_face_${i}_File_0.json`;
  });
  console.log('Fixed face:', m.face.length, 'items');
}

// Check if Motions_face_0_File_0.json exists, if not, copy from hair_0
const face0path = path.join(modelDir, 'Motions_face_0_File_0.json');
if (!fs.existsSync(face0path)) {
  console.log('Motions_face_0_File_0.json missing, copying from hair_0');
  fs.copyFileSync(path.join(modelDir, 'Motions_hair_0_File_0.json'), face0path);
}

fs.writeFileSync(path, JSON.stringify(j, null, 2), 'utf8');
console.log('All done');
