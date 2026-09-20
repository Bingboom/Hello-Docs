// Development-only: create the two teaching CSV inputs through Artifact Tool.
// The runnable demo itself uses only Python's standard library and TeX Live.
import fs from 'node:fs/promises';
import { Workbook } from '@oai/artifact-tool';
const root = new URL('./', import.meta.url);
if(process.argv.includes('--add-layout')){
  const target=new URL('data/products.csv',root);
  const wb=await Workbook.fromCSV(await fs.readFile(target,'utf8'),{sheetName:'products'});
  const sheet=wb.worksheets.getItemAt(0);
  const rows=sheet.getRange('A1:I4').values;
  if(rows[0][0]!=='record_id'||rows[0][8]!=='data_note')throw Error('Unexpected schema');
  const layouts={'DEMO-300':'hero','DEMO-500':'split','DEMO-1000':'cards'};
  sheet.getRange('J1:J4').values=[['layout'],...rows.slice(1).map(r=>[layouts[r[1]]])];
  // Return the teaching input to the scenario's starting price. Existing output history is preserved.
  for(let i=1;i<4;i++)if(rows[i][1]==='DEMO-500')sheet.getRange(`G${i+1}`).values=[[999]];
  wb.recalculate();
  const quote=v=>`"${String(v??'').replaceAll('"','""')}"`;
  await fs.writeFile(target,sheet.getRange('A1:J4').values.map(r=>r.map(quote).join(',')).join('\n')+'\n');
  console.log('Added per-record layout; restored teaching starting price 999; previous PDFs preserved.');
  process.exit(0);
}
const datasets = {
  products: [
    ['record_id','model_id','product_name','capacity_wh','rated_power_w','weight_kg','price_cny','asset','data_note','layout'],
    ['local-300','DEMO-300','小野 300',288,300,3.6,599,'xiaoye-300.png','教学虚构数据，非真实产品参数','hero'],
    ['local-500','DEMO-500','小野 500',512,500,5.2,999,'xiaoye-500.png','教学虚构数据，非真实产品参数','split'],
    ['local-1000','DEMO-1000','小野 1000',1024,1000,9.8,1599,'xiaoye-1000.png','教学虚构数据，非真实产品参数','cards'],
  ],
  content: [
    ['model_id','tagline','introduction_template','scene'],
    ['DEMO-300','轻装出游的小伙伴','把周末装进背包。{{product_name}} 以 {{weight_kg}} kg 的小巧身形，陪你开启轻装出游的想象。','轻装出游'],
    ['DEMO-500','周末露营的小帮手','找一片树荫，留一点时间。{{product_name}} 的 {{capacity_wh}} Wh 教学容量，让露营装备介绍一目了然。','周末露营'],
    ['DEMO-1000','多人营地的大块头','约上朋友，一起去野。{{product_name}} 以 {{rated_power_w}} W 的教学额定输出，演示多人营地的产品故事。','多人营地'],
  ],
};
await fs.mkdir(new URL('data/',root),{recursive:true});
for (const [name,rows] of Object.entries(datasets)) {
  const target = new URL(`data/${name}.csv`,root);
  try { await fs.access(target); throw new Error(`Refusing to overwrite ${target}`); }
  catch(e) { if(e.code !== 'ENOENT') throw e; }
  const wb=Workbook.create();
  const sheet=wb.worksheets.add(name);
  const range=sheet.getRangeByIndexes(0,0,rows.length,rows[0].length);
  range.values=rows;
  wb.recalculate();
  console.log((await wb.inspect({kind:'table',range:`${name}!A1:I4`,tableMaxRows:4,tableMaxCols:9,maxChars:2000})).ndjson);
  // CSV has no formatting/formulas. Serialize the authored typed cell matrix.
  const quote=v=>`"${String(v??'').replaceAll('"','""')}"`;
  await fs.writeFile(target,range.values.map(r=>r.map(quote).join(',')).join('\n')+'\n');
}
