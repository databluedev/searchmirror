import React from 'react';
import './style.scss';
import { Grid } from '@mui/material';
import EcomWidget from './components/ecom_widget';

const ReportManagement = (props) => {
    return (
        <>
            <section className="reportsCanvas">
                <div className="p-b20">
                    <Grid container spacing={3} className="projectSection">
                        {props.dynamicReport.length > 0 ?
                            props.dynamicReport.map((item, index) => (
                                <Grid
                                    item
                                    xs={12}
                                    md={12}
                                    lg={12}
                                    xl={12}
                                    key={`report-widget-${item.sheet_id ?? 'unknown'}-${index}`}
                                >
                                    <EcomWidget projectList={props.projectList} handleInitialise={props.handleInitialise} report={item} index={index} projectChange={props.basedata} loading={props.widLod} canDelete={props.canDelete} canRename={props.canRename} />
                                </Grid>
                            ))
                            :
                            <div className='position-absolute top-50 wd-subTitle' style={{ left: '45%' }}>No Report sheets are found</div>
                        }
                    </Grid>
                </div>
            </section>
        </>
    )
}

export default React.memo(ReportManagement);


