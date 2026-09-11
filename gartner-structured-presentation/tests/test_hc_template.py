import json, sys, tempfile, unittest
from pathlib import Path
from lxml import etree as E

SK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SK/'scripts'))
from build_hc_template import build
from validate_hc_template import check

class TemplateBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.data=self.root/'data.json'
        points=[]
        for ident,year,x,adoption in [('stable',2026,.3,'2 to 5 years'),('stable',2027,.3,'Less than 2 years'),('move',2026,1.2,'More than 10 years'),('move',2027,3.2,'2 to 5 years'),('new',2027,2.2,'5 to 10 years'),('removed',2026,4.2,'Less than 2 years'),('obsolete',2026,3.3,'Obsolete before plateau'),('obsolete',2027,3.5,'Obsolete before plateau')]:
            points.append(dict(technology_id=ident,year=year,name=ident.title(),stage=str(int(x)),years=adoption,source_pixel={'x':x,'y':1},normalized_plot={'x':x/5,'y':.5}))
        self.payload={'chart':{'points':points}};self.data.write_text(json.dumps(self.payload))
        self.out=self.root/'out'
    def generate(self):
        build(self.data,self.out,'Synthetic',[2026,2027],[0,1,2,3,4,5],shift_policy='stage-relative-v1')
        return self.out/'hc-comparison.svg',self.out/'hc-template-mapping.json'
    def test_portable_template_preserves_years_shapes_and_zero_migration(self):
        svg,mapping=self.generate();result=check(svg,mapping)
        self.assertEqual((result['technologies'],result['annual_markers'],result['migration_relations']),(5,8,2))
        r=E.parse(str(svg));self.assertFalse(r.xpath('//*[@id="migration-stable"]'))
        self.assertEqual(len(r.xpath('//*[@id="point-obsolete-2027"]/*[local-name()="text"]')),1)
        legend=' '.join(r.xpath('//*[@id="legend_1" or @id="legend_2"]//text()'))
        self.assertIn('2026 track',legend);self.assertIn('2027 track',legend);self.assertIn('Removed in 2027',legend)
        self.assertNotIn('Enterprise Networking',svg.read_text())
    def test_shape_colour_geometry_and_extra_facets_fail_gate(self):
        svg,mapping=self.generate();original=svg.read_bytes()
        for kind in ('shape','colour','point','curve','extra','obsolete','legend','false-arrow'):
            r=E.fromstring(original)
            if kind=='legend':r.xpath('//*[@id="line2d_49"]/*')[0].set('style','stroke:#000000')
            elif kind=='false-arrow':
                n=E.SubElement(r,'{http://www.w3.org/2000/svg}g');n.set('id','migration-stable');n.set('class','annual-connector')
            elif kind=='extra':
                n=E.SubElement(r,'{http://www.w3.org/2000/svg}g');n.set('data-hc-year','2026')
            elif kind=='curve':r.xpath('//*[@id="line2d_7"]/*')[0].set('d','M 0 0 L 1 1')
            elif kind=='obsolete':
                n=r.xpath('//*[@id="point-obsolete-2027"]/*')[0];n.text='×'
            else:
                n=r.xpath('//*[@id="point-move-2027"]')[0]
                if kind=='point':n.set('transform','translate(10 0)')
                elif kind=='colour':n[0].set('style','fill:#000000')
                else:n[0].set('d','M 0 0 L 1 1')
            svg.write_bytes(E.tostring(r))
            with self.subTest(kind=kind),self.assertRaises(ValueError):check(svg,mapping)
    def test_missing_policy_unknown_adoption_and_duplicate_points_fail(self):
        with self.assertRaises(ValueError):build(self.data,self.out,'Synthetic',[2026,2027],[0,1,2,3,4,5])
        self.payload['chart']['points'][0]['years']='Unknown';self.data.write_text(json.dumps(self.payload))
        with self.assertRaises(ValueError):self.generate()
        self.payload['chart']['points'][0]['years']='2 to 5 years';self.payload['chart']['points'].append(self.payload['chart']['points'][0]);self.data.write_text(json.dumps(self.payload))
        with self.assertRaises(ValueError):self.generate()
    def test_no_overwrite_and_no_source_mutation(self):
        original=self.data.read_bytes();self.generate()
        with self.assertRaises(FileExistsError):self.generate()
        self.assertEqual(original,self.data.read_bytes())

if __name__=='__main__':unittest.main()
