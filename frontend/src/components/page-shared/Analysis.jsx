import React from 'react';
import {Card} from '../Common';

export function Explainer({children}){return <p className="chart-explainer">{children}</p>}
export function ChartCard({title,sample,description,children}){return <Card title={title} className="analysis-card">{sample&&<p className="sample-note">{sample}</p>}{children}<Explainer>{description}</Explainer></Card>}
