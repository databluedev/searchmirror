import React, { useState, useEffect } from "react";
import { KNRSelectRegion } from "../../commonComponents/parts";

function CEditRegionList(props) {
    const rgoptions = props.regionData;
    const [fltrregion, setfltrRegion] = useState(props.regionData);
    const [region, setRegion] = useState(props.lastKwdRegion.region);
    const [isocode, setIsocode] = useState(props.lastKwdRegion.isocode);
    const [countryname, setCountryname] = useState(props.lastKwdRegion.countryname);
    const regionValue = region !== "" ? `${isocode} ${region} (${countryname})` : countryname;
    const optionAvailable = Array.isArray(rgoptions) && rgoptions.some(
        (option) => `${option.Rcd} ${option.RN} (${option.Rcnt})` === regionValue
    );

    const rgselectlstChange = (event) => {
        const { target: { value }, } = event;
        const slctdRgn = value.split("(")
        const cntry = slctdRgn[1].replace(')', '')
        const isorgn = slctdRgn[0].split(" ")
        setRegion(isorgn[1]);
        setCountryname(cntry);
        setIsocode(isorgn[0]);
        props.rgDataUpdate(
            {
                countryname: cntry,
                region: isorgn[1],
                isocode: isorgn[0]
            })
    }

    const regionListdataUpdate = (data) => {
        setfltrRegion(data);
    }

    const menuOpen = () => {
        setfltrRegion(rgoptions);
    }

    useEffect(() => {
        setRegion(props.lastKwdRegion.region);
        setIsocode(props.lastKwdRegion.isocode);
        setCountryname(props.lastKwdRegion.countryname);
    }, [props.lastKwdRegion]);

    return (
        <>
            <div className="cursorP">
                <KNRSelectRegion rgName="kr_rgrndrName text-truncate" className="knrRegion" placeholder={"Region"} menuOpen={menuOpen} fullList={rgoptions} menulist={fltrregion} value={optionAvailable ? regionValue : ""} onchange={rgselectlstChange} regionUpdate={regionListdataUpdate} rgcode={isocode} rgname={region} rgcnt={countryname} />
            </div>
        </>
    );
}

export default CEditRegionList; 
