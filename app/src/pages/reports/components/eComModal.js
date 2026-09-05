import { Backdrop, Button, Fade, Grid, Modal } from "@mui/material";
import { Box } from "@mui/system";
import { Para, Title } from "../../commonComponents/parts";
import { CloseIconlg } from "../../commonComponents/icons";
import ERankForm from "../eComSheets/e_com_rank_form";
import EBaseForm from "../eComSheets/e_com_base_form";
import EOverviewForm from "../eComSheets/e_com_overview_form";

function EcomModal(props) {
    const {open, handleClose, style, filterMenu, handleFilter, setData, isGa, isGsc, summaryList} = props
    return (
        <Modal
            className="full-page-modal"
            open={open}
            onClose={handleClose}
            aria-labelledby="ecommerce-report-modal-title"
            aria-describedby="ecommerce-report-modal-description"
            closeAfterTransition
            BackdropComponent={Backdrop}
            BackdropProps={{
                timeout: 1000,
            }}
        >
            <Fade in={open} {...(open ? { timeout: 750 } : { timeout: 1000 })}>
                <Box className="fp-modal-box drp-modal" sx={style}>
                    <header className="fp-modal-header">
                        <div className="d-flex align-items-center justify-content-between px-2">
                            <div>
                                <Title id="ecommerce-report-modal-title" class="fp-modal-title">
                                    {"Configure Report"}
                                </Title>
                                <Para id="ecommerce-report-modal-description" class="fp-modal-sub-title mb-0">
                                    {"Customize and control reports to fit your unique requirements."}
                                </Para>
                            </div>

                            <div style={{ flex: "0 0 auto" }}>
                                <Button aria-label="Close report configuration" onClick={handleClose} className="wd-CloseButton">
                                    <CloseIconlg color="#0a0a0a" />
                                </Button>
                            </div>
                        </div>
                    </header>

                    <section className="drp-form">
                        <div className="px-2 m-b70">

                            <Grid container spacing={3} className="drp-main-grid">
                                <Grid className="drp-filter-grid" item xs={12} md={12} lg={12}>

                                    {/* Same picker as the non-ecommerce modal, and the same
                                        reasoning: the styles live in pages/reports/style.scss,
                                        the two buildable types lead, and Domain Metrics is
                                        marked unavailable because nothing writes the Moz /
                                        Ahrefs / PageSpeed columns it reads. */}
                                    <div className="wd-history-duration-filter reportTypePicker">
                                        <div className="d-flex align-items-center flex-wrap bg-transparent">

                                            <label className={filterMenu === "rank" ? "wd-filterLabel active" : "wd-filterLabel"}>
                                                <input type="radio" name="report-type" value="rank" checked={filterMenu === "rank"} onChange={() => handleFilter("rank")} />
                                                <div className="wd-filterOption">
                                                    <span>Keyword Ranking</span>
                                                </div>
                                            </label>

                                            <label className={filterMenu === "overview" ? 'wd-filterLabel active' : "wd-filterLabel"}>
                                                <input type="radio" name="report-type" value="overview" checked={filterMenu === "overview"} onChange={() => handleFilter("overview")} />
                                                <div className='wd-filterOption'>
                                                    <span className=''>Summary</span>
                                                </div>
                                            </label>

                                            <label className="wd-filterLabel disabled" title="Needs a Moz or Ahrefs connection, which this instance does not have">
                                                <input type="radio" name="report-type" value="base" disabled />
                                                <div className="wd-filterOption">
                                                    <span>Domain Metrics <small>(Moz/Ahrefs later)</small></span>
                                                </div>
                                            </label>

                                            <label className="wd-filterLabel disabled" title="Available after Google OAuth is added">
                                                <input type="radio" name="report-type" value="gsc" disabled />
                                                <div className="wd-filterOption">
                                                    <span>Google Search Console <small>(OAuth later)</small></span>
                                                </div>
                                            </label>

                                            <label className="wd-filterLabel disabled" title="Available after Google OAuth is added">
                                                <input type="radio" name="report-type" value="ga" disabled />
                                                <div className="wd-filterOption">
                                                    <span>Google Analytics <small>(OAuth later)</small></span>
                                                </div>
                                            </label>

                                        </div>
                                    </div>
                                </Grid>
                                <Grid className="drp-content-grid" item xs={12} md={12} lg={12}>
                                    <div className="drp-content-block">
                                        {filterMenu === "rank" ?
                                                <ERankForm handleClose={handleClose} setData={setData} />

                                            : filterMenu === "base" ?
                                                <EBaseForm handleClose={handleClose} setData={setData} />
                                                :
                                                        <EOverviewForm summaryList={summaryList} handleClose={handleClose} setData={setData} isGa={isGa} isGsc={isGsc} />
                                        }

                                    </div>
                                </Grid>
                            </Grid>
                        </div>
                    </section>
                </Box>
            </Fade>
        </Modal>
    )
}
export default EcomModal;
