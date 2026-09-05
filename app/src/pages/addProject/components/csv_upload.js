import React, { useState } from "react";
// import { useHistory } from "react-router-dom";
// import Cookies from 'universal-cookie';
// import axios from 'axios';
import { toast } from 'react-toastify';
import { FileUploadIcon, BacklinkIcon  } from "../../commonComponents/icons";
// import {fstLtrCapitalfun} from "../../common_fun";   

// import { styled } from "@mui/material/styles";
import { Box, Button, Modal, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from "@mui/material";
import { AppButton, SmallText, Title, Para, AppIconButton,} from "../../commonComponents/parts";
import { Input } from "@/components/ui/input";


const style = {
  position: "absolute",
  width: "100%",
  height: "100%",
  bgcolor: "var(--paper)",
  padding: '25px 25px 25px 85px',
  outline: "none"
};


export const CsvUpload = (props) => {

    const [loading, setLoading] = useState("");
    const [csvArray, setCsvArray] = useState([]); 
    // const [txtArray, setTxtArray] = useState([]); 
    const txtArrayFull = useState([]); 
    const [csvHeader, setCsvHeader] = useState([]);
    const [step, setStep] = useState("");
    const [filetype, setFiletype] = useState("");
    const [selectedcolumn, setSltcolumn] = useState("");
    const [displaykwlist, setdsplykwlist] = useState(props.keywordlist);
    const [selectkwlist, setSltkwlist] = useState(props.keywordlist);
    const [selectkwlistFull, setSltkwlistfull] = useState(props.keywordlist);
    const [searchVal, setSearchVal] = useState("");

    const [open, setOpen] = useState(false);
    // const handleOpen = () => setOpen(true);
    const handleClose = () => setOpen(false);

    // useEffect(() => {
    //   setSltkwlist(props.keywordlist);
    //   setOpen(false)

    // }, [props]);

    const validateData = (strData, type) => {
      if (type === "array") {
        const eachObject = strData.map( row => {
          const rData = row.replaceAll('"', '')
          rData.replace(/^['](.+(?=[']$))[']$/, '$1')
          rData.trim()
            return rData.toLowerCase() 
          }, {})
          return eachObject 
      } else {
        if (strData !== undefined) {
          const rData = strData.replaceAll('"', '')
          rData.replace(/^["'](.+)['"]$/,'$1'); 
          rData.trim(); 
          return rData.toLowerCase(); 
        }
        return null
      }
    }

    const processCSV = (str, delim=',') => {

        // const headers = str.slice(0,str.indexOf('\n')).split(delim);
        const hString = str.slice(0,str.indexOf('\n'));
        const hSlice = hString.split(delim); 
        const headers = validateData(hSlice, "array")

        setCsvHeader(headers)
        setSltcolumn(headers[0])
        const rows = str.slice(str.indexOf('\n')+1).split('\n');

        const newArray = rows.map( row => {
            const values = row.split(delim);
            const eachObject = headers.reduce((obj, header, i) => {
              // obj[header] = values[i]; 
              obj[header] = validateData(values[i], null); 
              return obj;
            }, {})
            return eachObject;
        })         
        setCsvArray(newArray)
        setOpen(true)
        setStep("csv")
    }

    const processColumn = () => {
        const el = csvArray.map((row, key) => {
          return (row.hasOwnProperty(selectedcolumn) && row[selectedcolumn]) ? row[selectedcolumn].trim() : null
        })
        var kws = [...new Set([...props.keywordlist,...el])].filter(x => x)
        setSltkwlist(kws)
        setSltkwlistfull(kws)
        setdsplykwlist(kws)
        setStep("txt")
    }

    const processTXT = (str) => {
        var lines = str.split('\n');
        const newArray = lines.map( row => {
          return validateData(row, null)
        }, {})
        var kws = [...new Set([...props.keywordlist,...newArray])].filter(x => x)
        setSltkwlist(kws)
        setSltkwlistfull(kws)
        setdsplykwlist(kws)
        setOpen(true)
        setStep("txt")
    }

    const onInputClear = (event) => {
        event.target.value = ''
        setSltkwlist(props.keywordlist);
        setSltkwlistfull(props.keywordlist);
        setdsplykwlist(props.keywordlist);
        setSearchVal("")
        // setTxtArray([])
        // setTxtArrayfull([])
    }

    const onFileSubmit = (e) => {
        e.preventDefault()
        setLoading("LOADING") 
        // setCsvFile(e.target.files[0])

        const imageMimeType = ["text/csv", "text/plain"] 
        const imageExtType = ["csv", "txt"] 
        const file = e.target.files[0];

        if (file) { 
            const fileExtension = file?.name.split(".")[1];
          
            if (!imageExtType.includes(fileExtension.trim())) {
              toast.error("Invalid File"); 
              setLoading("ERROR") 
              return true;
            }

            if (!imageMimeType.includes(file.type.trim())) {
              toast.error("Invalid File Type");
              setLoading("ERROR") 
              return true; 
            } 

            // console.log(file.size);
            if (parseInt(file.size) > 500000) {
              toast.error("Maximum File Size 500KB");
              setLoading("ERROR")
              return true;
            } 
            

            // var checkFlag = 0;
            const reader = new FileReader();
            reader.readAsText(file);  
            reader.onload = function(e) {
                const text = e.target.result;

                if (file.type.trim() === "text/csv") {
                    processCSV(text)
                    setFiletype("CSV")
                    // checkFlag = 1;
                    setLoading("DONE") 
                } else if (file.type.trim() === "text/plain") {
                    processTXT(text) 
                    setFiletype("Text")
                    // checkFlag = 1;
                    setLoading("DONE")
                } else {
                    toast.error("File not supported")
                    setLoading("File not supported")
                }
            }
        return true;
        }
      
    }

    const keywordDelete = (delkw) => {
        var selectkw = [...selectkwlist.filter((kw, index) => kw !== delkw)];
        setSltkwlist(selectkw)
        // setSltkwlistfull([...selectkwlistFull.filter((kw, index) => kw !== delkw)])
        // // props.kwupdatefun(selectkw)
        // if (txtArray.filter(e => e === delkw).length === 0) {
        //     setTxtArray([...txtArray, delkw]);
        //     setTxtArrayfull([...txtArrayFull, delkw]);
        // }
    };

    const keywordAdd= (addkw) => {
        setSltkwlist([...selectkwlist, addkw.toLowerCase()])
        // setSltkwlistfull([...selectkwlistFull, addkw.toLowerCase()])
        // setTxtArray([...txtArray.filter((kw, index) => kw !== addkw)]);
        // setTxtArrayfull([...txtArrayFull.filter((kw, index) => kw !== addkw)]);


        // if(selectkwlist.length < props.limit){

        //     if (selectkwlist.filter(e => e.toLowerCase() === addkw.toLowerCase()).length === 0) {
        //         var selectkw = [...selectkwlist, addkw.toLowerCase()]
        //         setSltkwlist(selectkw.filter(x => x !== null))
        //         // props.kwupdatefun(selectkw)
        //     }else{
        //         toast.error("The keyword is already added.")
        //     }
        //     setTxtArray([...txtArray.filter((kw, index) => kw !== addkw)]);
        //     setTxtArrayfull([...txtArray.filter((kw, index) => kw !== addkw)]);
        // } else{
        //     toast.error("You have reached the maximum number of keywords entered.")
        // }
    };

    const searchupdate = (e) => {
        setSearchVal(e.target.value)

        if(e.target.value === ""){
            setdsplykwlist(selectkwlistFull);
            // setSltkwlist(selectkwlistFull);
            // setTxtArray(txtArrayFull);
        }else{
            // var output = txtArrayFull.filter((row) => { return row ? row.toLowerCase().includes(e.target.value.toLowerCase()) : null });
            // setTxtArray(output);
            var selectkw = selectkwlistFull.filter((row) => { return row ? row.toLowerCase().includes(e.target.value.toLowerCase()) : null });
            setdsplykwlist(selectkw);
            // setSltkwlist(selectkw);
        }
    }

    const selectallkw = () => {
        setSltkwlist([...selectkwlistFull, ...txtArrayFull]);
        // setSltkwlistfull([...selectkwlistFull, ...txtArrayFull]);
        // setTxtArray([]);
        // setTxtArrayfull([])

        // if(selectkwlist.length <= props.limit){
        //     setSltkwlist(txtArrayFull.filter(x => x !== null))
        //     setTxtArray([])
        //     setTxtArrayfull([])
        // }else{
        //     // var count =  props.limit - selectkwlist.length
        //     toast.error("You have reached the maximum number of keywords entered.")
        // }

    }

    const importkwfun = () => {
        if(selectkwlist.length <= props.limit){
            props.kwupdatefun(selectkwlist); 
            setOpen(false);
        }else{
            var count =  selectkwlist.length - props.limit
            // toast.error("You have reached the maximum number of keywords entered.")
            toast.error("Please deselect "+count+" keywords.")
        }
    }

    const viewchange = () => {
        if (filetype === "CSV" && step === 'txt'){
            setStep("csv");
        }else{
            handleClose();
        }
    }

    return (
      <div className="text-right">
        <label htmlFor="btn-upload">
            <input id="btn-upload" accept=".csv, .txt" type="file" onChange={(e) => {onFileSubmit(e)}} onClick={onInputClear} hidden />
            <Box
              sx={{
                display: "flex",
                flexWrap: "wrap",
                gap: "10px",
              }}
            >
            <Button
               color="white"
               className="borderBtn minW150x darkgray"
               variant="contained"
               component="div"
             > 
              {/*<span className="loading" />*/}
              { loading === "LOADING" ? 
                <span> Loading... </span> 
              : 
                <>
                <span className="m-r10 mb-1"><FileUploadIcon /></span>
                CSV or Text
                </>
              }
             </Button>
             </Box>
        </label> 

        <Modal
          open={open}
          onClose={handleClose}
          aria-labelledby="modal-modal-title"
          aria-describedby="modal-modal-description"
        >
          <Box className="addProject" sx={style}>
            <div>
              <header className="p-0">
                <div className="d-flex align-items-center justify-content-between">
                  <div className="d-flex align-items-center gap-3">
                    <span className={(filetype === "CSV" && step === "txt") ? "" : "d-none"}>
                      <AppIconButton
                        onclick={viewchange}
                        Icon={<BacklinkIcon />}
                      />
                    </span>
                    <div>
                      <Title class="mb-0 lineHAuto">{filetype} Upload</Title>
                      <Para class="mb-0">Select the appropriate column which has all your keywords</Para>
                    </div>
                  </div>

                  <div style={{ flex: "0 0 auto" }}>
                    <Button onClick={handleClose}>
                      {/*<CloseIcon />*/}
                      <svg style={{ color: "var(--ink)" }}
                        id="Component_69_46"
                        data-name="Component 69 – 46"
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 16 16"
                      >
                        <path
                          id="Path_410"
                          data-name="Path 410"
                          d="M13.4,12l6.3-6.3a.99.99,0,0,0-1.4-1.4L12,10.6,5.7,4.3A.99.99,0,0,0,4.3,5.7L10.6,12,4.3,18.3A.908.908,0,0,0,4,19a.945.945,0,0,0,1,1,.908.908,0,0,0,.7-.3L12,13.4l6.3,6.3a.967.967,0,0,0,1.4,0,.967.967,0,0,0,0-1.4Z"
                          transform="translate(-4 -4)"
                          fill="currentColor"
                        />
                      </svg>
                    </Button>
                  </div>
                </div>
              </header>

              { step === "csv" ? 

                <div>
                  <TableContainer style={{background: 'var(--surface)'}}>
                    <Table stickyHeader aria-label="sticky table">
                      <TableHead>
                        <TableRow>
                          {
                            csvHeader.map((item, i) => (
                                <TableCell align="center" key={i}>
                                  <div className="customRadio">
                                    <label className="labl">
                                      <input
                                        type="checkbox"
                                        name="radioname"
                                        value={item}
                                        checked={selectedcolumn === item}
                                        onChange={(e) => {setSltcolumn(item)}}
                                        // onClick={(e) => {processColumn(item)}}
                                      />
                                      <div>
                                        <span className="border" />
                                        {item}
                                      </div>
                                    </label>
                                  </div>
                                </TableCell>
                            ))
                          }

                        </TableRow>
                      </TableHead>
                      <TableBody>

                        {csvArray.map((row, i) => (
                          <TableRow
                            key={i}
                            sx={{
                              "&:last-child td, &:last-child th": { border: 0 },
                            }}
                          >
                            {csvHeader.map((item, i) => (
                                <TableCell align="center" key={i}>
                                    {row[item]}
                                </TableCell>
                            ))}
                           
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </div>

              : step === "txt" ?

                <section className="keyword">

                  <div className="d-flex justify-content-between align-items-center flex-wrap gap-3">
                    <div className="d-flex align-items-center">
                      <Box
                        className="flexoAuto m-r10"
                        sx={{
                          width: "400px",
                          "@media screen and (max-width: 575.98px)": {
                            width: "auto",
                          },
                        }}
                      >
                        <Input
                          type="search"
                          className="search w-full"
                          id="outlined-basic"
                          placeholder="Search"
                          value={searchVal}
                          onChange={searchupdate}
                          autoComplete="off"
                        />
                      </Box>
                    </div>

                    <div className="d-flex align-items-center">
                      <SmallText class="d-flex justify-content-end flexoAuto m-r10 m-b0">
                        Remaining:{" "}
                        <span className="txtClr m-l5 fM">{props.limit - selectkwlist.length} keywords</span>
                      </SmallText>

                      <Box sx={{minWidth: '80px'}}>
                      <AppButton
                        class="secondaryBtn lighthover"
                        noIcon="m-0"
                        value="Reset"
                        onclick={selectallkw}
                      ></AppButton>
                      </Box>
                    </div>
                  </div>

                  <Box
                    className="box"
                    sx={{
                      minHeight: "calc(100vh - 250px) !important",
                      maxHeight: "calc(100vh - 250px) !important",
                    }}
                  >
                    <Box
                      sx={{
                        display: "flex",
                        flexWrap: "wrap",
                        gap: "10px",
                      }}
                    >
                      {displaykwlist.map((kw, index) => (
                        (kw !== null && kw !== "" && selectkwlist.includes(kw)) ?
                        <div className="tag new p-2 cursorP" key={index} onClick={() => keywordDelete(kw)}>
                          {kw}
                        </div>
                      : 
                        <div className="tag p-2 cursorP" key={index} onClick={() => keywordAdd(kw)}>
                          {kw}
                        </div>
                      ))}

                      {/*selectkwlist.map((kw, index) => (
                        kw !== null && kw !== "" ?
                        <div className="tag new p-2 cursorP" key={index} onClick={() => keywordDelete(kw)}>
                          {kw}
                        </div>
                        : null                          
                      ))*/}

                      {/*txtArray.map((kw, index) => (
                        kw !== null && kw !== "" ? 
                        <div className="tag p-2 cursorP" key={index} onClick={() => keywordAdd(kw)}>
                          {kw}
                        </div>
                        : null          
                      ))*/}
                      
                    </Box>
                  </Box>

                </section>
              : null
              }

            </div>
            <section className="footer full">
              <div>
                <AppButton
                  value="Cancel"
                  color="white"
                  class="borderBtn"
                  noIcon="d-none"
                  onclick={handleClose}
                ></AppButton>
              </div>
              <div>
                { step === "csv" ?
                  <AppButton
                    value="Next"
                    class=""
                    noIcon="d-none"
                    onclick={processColumn}
                  ></AppButton>
                :
                  <AppButton
                    value="Confirm"
                    class=""
                    noIcon="d-none"
                    onclick={importkwfun}
                  ></AppButton>
                }
              </div>
            </section>
          </Box>
        </Modal>
      </div>
    );
};

