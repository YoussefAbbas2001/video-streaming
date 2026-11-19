// Writes the deck's colour scheme and fonts into ppt/theme/*.xml (pptxgenjs cannot write theme colours itself).
const fs = require("fs");
const JSZip = require(require.resolve("jszip", { paths: [require.resolve("pptxgenjs")] }));

const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const SLOTS = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"];

async function writeTheme(file, theme) {
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const parts = Object.keys(zip.files).filter((n) => /^ppt\/theme\/theme\d+\.xml$/.test(n));
  for (const name of parts) {
    let xml = await zip.file(name).async("string");
    const scheme = `<a:clrScheme name="${esc(theme.name)}">` +
      SLOTS.map((k) => `<a:${k}><a:srgbClr val="${theme.colors[k]}"/></a:${k}>`).join("") + `</a:clrScheme>`;
    xml = xml.replace(/<a:clrScheme[\s\S]*?<\/a:clrScheme>/, scheme);
    xml = xml.replace(/(<a:majorFont>\s*<a:latin typeface=")[^"]*"/, `$1${esc(theme.headFontFace)}"`);
    xml = xml.replace(/(<a:minorFont>\s*<a:latin typeface=")[^"]*"/, `$1${esc(theme.bodyFontFace)}"`);
    xml = xml.replace(/(<a:theme[^>]*\sname=")[^"]*"/, `$1${esc(theme.name)}"`);
    zip.file(name, xml);
  }
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}
module.exports = { writeTheme };
