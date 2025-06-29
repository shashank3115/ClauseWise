import jsPDF from 'jspdf';

interface FlaggedClause {
    clause_text: string;
    issue: string;
    severity: 'low' | 'medium' | 'high';
}

interface ComplianceIssue {
    law: string;
    missing_requirements: string[];
    recommendations: string[];
}

interface AnalysisResult {
    summary: string;
    flagged_clauses: FlaggedClause[];
    compliance_issues: ComplianceIssue[];
    jurisdiction: string;
}

interface ComplianceRiskScore {
    overall_score: number;
    financial_risk_estimate: number;
    violation_categories: string[];
    jurisdiction_risks: Record<string, number>;
}

export class PDFReportGenerator {
    private doc: jsPDF;
    private pageHeight: number;
    private pageWidth: number;
    private margin: number;
    private currentY: number;
    private lineHeight: number;

    constructor() {
        this.doc = new jsPDF();
        this.pageHeight = this.doc.internal.pageSize.height;
        this.pageWidth = this.doc.internal.pageSize.width;
        this.margin = 20;
        this.currentY = this.margin;
        this.lineHeight = 7;
    }

    private addNewPageIfNeeded(requiredHeight: number): void {
        if (this.currentY + requiredHeight > this.pageHeight - this.margin) {
            this.doc.addPage();
            this.currentY = this.margin;
        }
    }

    private getJurisdictionName(code: string): string {
        const jurisdictionNames: Record<string, string> = {
            MY: 'Malaysia',
            SG: 'Singapore',
            EU: 'European Union',
            US: 'United States'
        };
        return jurisdictionNames[code] || code;
    }

    private getSeverityColor(severity: string): [number, number, number] {
        switch (severity) {
            case 'high':
                return [220, 38, 127]; // Red
            case 'medium':
                return [245, 158, 11]; // Amber
            case 'low':
                return [34, 197, 94]; // Green
            default:
                return [107, 114, 128]; // Gray
        }
    }

    private getRiskScoreColor(score: number): [number, number, number] {
        if (score >= 80) return [220, 38, 127]; // High risk - Red
        if (score >= 60) return [245, 158, 11]; // Medium risk - Amber
        if (score >= 40) return [234, 179, 8]; // Medium-low risk - Yellow
        return [34, 197, 94]; // Low risk - Green
    }

    private wrapText(text: string, maxWidth: number): string[] {
        const words = text.split(' ');
        const lines: string[] = [];
        let currentLine = '';

        for (const word of words) {
            const testLine = currentLine + (currentLine ? ' ' : '') + word;
            const textWidth = this.doc.getStringUnitWidth(testLine) * (this.doc as any).getFontSize() / this.doc.internal.scaleFactor;
            
            if (textWidth > maxWidth && currentLine) {
                lines.push(currentLine);
                currentLine = word;
            } else {
                currentLine = testLine;
            }
        }
        
        if (currentLine) {
            lines.push(currentLine);
        }
        
        return lines;
    }

    private addHeader(): void {
        // Company/App Name
        this.doc.setFontSize(24);
        this.doc.setFont('helvetica', 'bold');
        this.doc.setTextColor(59, 130, 246); // Blue color
        this.doc.text('LegalGuard RegTech', this.margin, this.currentY);
        
        this.currentY += 15;
        
        // Report Title
        this.doc.setFontSize(18);
        this.doc.setTextColor(0, 0, 0);
        this.doc.text('Contract Analysis Report', this.margin, this.currentY);
        
        this.currentY += 10;
        
        // Date
        this.doc.setFontSize(12);
        this.doc.setFont('helvetica', 'normal');
        this.doc.setTextColor(107, 114, 128);
        const currentDate = new Date().toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        this.doc.text(`Generated on: ${currentDate}`, this.margin, this.currentY);
        
        this.currentY += 15;
        
        // Add a horizontal line
        this.doc.setDrawColor(229, 231, 235);
        this.doc.line(this.margin, this.currentY, this.pageWidth - this.margin, this.currentY);
        this.currentY += 10;
    }

    private addSummarySection(result: AnalysisResult): void {
        this.addNewPageIfNeeded(40);
        
        // Section header
        this.doc.setFontSize(16);
        this.doc.setFont('helvetica', 'bold');
        this.doc.setTextColor(59, 130, 246);
        this.doc.text('Executive Summary', this.margin, this.currentY);
        this.currentY += 10;
        
        // Jurisdiction
        this.doc.setFontSize(12);
        this.doc.setFont('helvetica', 'bold');
        this.doc.setTextColor(0, 0, 0);
        this.doc.text(`Jurisdiction: ${this.getJurisdictionName(result.jurisdiction)}`, this.margin, this.currentY);
        this.currentY += 10;
        
        // Summary text
        this.doc.setFont('helvetica', 'normal');
        this.doc.setTextColor(55, 65, 81);
        const summaryLines = this.wrapText(result.summary, this.pageWidth - 2 * this.margin);
        
        for (const line of summaryLines) {
            this.addNewPageIfNeeded(this.lineHeight);
            this.doc.text(line, this.margin, this.currentY);
            this.currentY += this.lineHeight;
        }
        
        this.currentY += 10;
    }

    private addRiskScoreSection(riskScore: ComplianceRiskScore): void {
        this.addNewPageIfNeeded(60);
        
        // Section header
        this.doc.setFontSize(16);
        this.doc.setFont('helvetica', 'bold');
        this.doc.setTextColor(147, 51, 234); // Purple
        this.doc.text('Compliance Risk Assessment', this.margin, this.currentY);
        this.currentY += 15;
        
        // Overall Risk Score Box
        const boxWidth = 60;
        const boxHeight = 30;
        const boxX = this.margin;
        const boxY = this.currentY - 5;
        
        // Draw risk score box
        const [r, g, b] = this.getRiskScoreColor(riskScore.overall_score);
        this.doc.setFillColor(r, g, b);
        this.doc.setDrawColor(r, g, b);
        this.doc.roundedRect(boxX, boxY, boxWidth, boxHeight, 3, 3, 'FD');
        
        // Risk score text
        this.doc.setFontSize(20);
        this.doc.setFont('helvetica', 'bold');
        this.doc.setTextColor(255, 255, 255);
        this.doc.text(`${riskScore.overall_score}%`, boxX + boxWidth/2, boxY + boxHeight/2, { align: 'center' });
        
        // Risk label
        this.doc.setFontSize(10);
        this.doc.text('Risk Score', boxX + boxWidth/2, boxY + boxHeight/2 + 8, { align: 'center' });
        
        // Financial risk estimate
        this.doc.setFontSize(12);
        this.doc.setFont('helvetica', 'bold');
        this.doc.setTextColor(0, 0, 0);
        this.doc.text('Financial Risk Estimate:', boxX + boxWidth + 20, boxY + 10);
        
        this.doc.setFont('helvetica', 'normal');
        this.doc.setTextColor(220, 38, 127);
        const financialRisk = new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(riskScore.financial_risk_estimate);
        this.doc.text(financialRisk, boxX + boxWidth + 20, boxY + 22);
        
        this.currentY += boxHeight + 15;
        
        // Violation Categories
        if (riskScore.violation_categories.length > 0) {
            this.doc.setFontSize(14);
            this.doc.setFont('helvetica', 'bold');
            this.doc.setTextColor(0, 0, 0);
            this.doc.text('Violation Categories:', this.margin, this.currentY);
            this.currentY += 8;
            
            this.doc.setFontSize(11);
            this.doc.setFont('helvetica', 'normal');
            this.doc.setTextColor(55, 65, 81);
            
            for (const category of riskScore.violation_categories) {
                this.addNewPageIfNeeded(this.lineHeight);
                this.doc.text(`• ${category}`, this.margin + 5, this.currentY);
                this.currentY += this.lineHeight;
            }
            this.currentY += 5;
        }
        
        this.currentY += 10;
    }

    private addFlaggedClausesSection(flaggedClauses: FlaggedClause[]): void {
        this.addNewPageIfNeeded(30);
        
        // Section header
        this.doc.setFontSize(16);
        this.doc.setFont('helvetica', 'bold');
        this.doc.setTextColor(245, 158, 11); // Amber
        this.doc.text(`Flagged Clauses (${flaggedClauses.length})`, this.margin, this.currentY);
        this.currentY += 15;
        
        if (flaggedClauses.length === 0) {
            this.doc.setFontSize(12);
            this.doc.setFont('helvetica', 'normal');
            this.doc.setTextColor(34, 197, 94); // Green
            this.doc.text('✓ No flagged clauses found - All clauses appear to be compliant', this.margin, this.currentY);
            this.currentY += 15;
            return;
        }
        
        for (let i = 0; i < flaggedClauses.length; i++) {
            const clause = flaggedClauses[i];
            this.addNewPageIfNeeded(40);
            
            // Clause number and severity
            this.doc.setFontSize(12);
            this.doc.setFont('helvetica', 'bold');
            this.doc.setTextColor(0, 0, 0);
            this.doc.text(`Clause ${i + 1}:`, this.margin, this.currentY);
            
            // Severity badge
            const [r, g, b] = this.getSeverityColor(clause.severity);
            this.doc.setFillColor(r, g, b);
            this.doc.setTextColor(255, 255, 255);
            this.doc.setFontSize(10);
            const severityText = clause.severity.toUpperCase();
            const severityWidth = this.doc.getStringUnitWidth(severityText) * 10 / this.doc.internal.scaleFactor + 4;
            this.doc.roundedRect(this.margin + 50, this.currentY - 4, severityWidth, 8, 2, 2, 'F');
            this.doc.text(severityText, this.margin + 52, this.currentY + 1);
            
            this.currentY += 12;
            
            // Issue description
            this.doc.setFontSize(11);
            this.doc.setFont('helvetica', 'bold');
            this.doc.setTextColor(220, 38, 127); // Red
            const issueLines = this.wrapText(clause.issue, this.pageWidth - 2 * this.margin);
            for (const line of issueLines) {
                this.addNewPageIfNeeded(this.lineHeight);
                this.doc.text(line, this.margin, this.currentY);
                this.currentY += this.lineHeight;
            }
            
            this.currentY += 3;
            
            // Clause text
            this.doc.setFont('helvetica', 'normal');
            this.doc.setTextColor(75, 85, 99);
            const clauseText = clause.clause_text.length > 300 
                ? clause.clause_text.substring(0, 300) + '...' 
                : clause.clause_text;
            const clauseLines = this.wrapText(`"${clauseText}"`, this.pageWidth - 2 * this.margin - 10);
            
            for (const line of clauseLines) {
                this.addNewPageIfNeeded(this.lineHeight);
                this.doc.text(line, this.margin + 5, this.currentY);
                this.currentY += this.lineHeight;
            }
            
            this.currentY += 10;
        }
    }

    private addComplianceIssuesSection(complianceIssues: ComplianceIssue[]): void {
        this.addNewPageIfNeeded(30);
        
        // Section header
        this.doc.setFontSize(16);
        this.doc.setFont('helvetica', 'bold');
        this.doc.setTextColor(147, 51, 234); // Purple
        this.doc.text(`Compliance Issues (${complianceIssues.length})`, this.margin, this.currentY);
        this.currentY += 15;
        
        if (complianceIssues.length === 0) {
            this.doc.setFontSize(12);
            this.doc.setFont('helvetica', 'normal');
            this.doc.setTextColor(34, 197, 94); // Green
            this.doc.text('✓ No compliance issues found - Contract meets all regulatory requirements', this.margin, this.currentY);
            this.currentY += 15;
            return;
        }
        
        for (const issue of complianceIssues) {
            this.addNewPageIfNeeded(50);
            
            // Law name
            this.doc.setFontSize(14);
            this.doc.setFont('helvetica', 'bold');
            this.doc.setTextColor(0, 0, 0);
            this.doc.text(issue.law, this.margin, this.currentY);
            this.currentY += 12;
            
            // Missing requirements
            if (issue.missing_requirements.length > 0) {
                this.doc.setFontSize(12);
                this.doc.setFont('helvetica', 'bold');
                this.doc.setTextColor(220, 38, 127); // Red
                this.doc.text('Missing Requirements:', this.margin, this.currentY);
                this.currentY += 8;
                
                this.doc.setFontSize(11);
                this.doc.setFont('helvetica', 'normal');
                this.doc.setTextColor(55, 65, 81);
                
                for (const requirement of issue.missing_requirements) {
                    const reqLines = this.wrapText(`✗ ${requirement}`, this.pageWidth - 2 * this.margin - 10);
                    for (const line of reqLines) {
                        this.addNewPageIfNeeded(this.lineHeight);
                        this.doc.text(line, this.margin + 5, this.currentY);
                        this.currentY += this.lineHeight;
                    }
                }
                this.currentY += 5;
            }
            
            // Recommendations
            if (issue.recommendations.length > 0) {
                this.doc.setFontSize(12);
                this.doc.setFont('helvetica', 'bold');
                this.doc.setTextColor(34, 197, 94); // Green
                this.doc.text('Recommendations:', this.margin, this.currentY);
                this.currentY += 8;
                
                this.doc.setFontSize(11);
                this.doc.setFont('helvetica', 'normal');
                this.doc.setTextColor(55, 65, 81);
                
                for (const recommendation of issue.recommendations) {
                    const recLines = this.wrapText(`✓ ${recommendation}`, this.pageWidth - 2 * this.margin - 10);
                    for (const line of recLines) {
                        this.addNewPageIfNeeded(this.lineHeight);
                        this.doc.text(line, this.margin + 5, this.currentY);
                        this.currentY += this.lineHeight;
                    }
                }
                this.currentY += 5;
            }
            
            this.currentY += 10;
        }
    }

    private addFooter(): void {
        const pageCount = (this.doc as any).getNumberOfPages();
        
        for (let i = 1; i <= pageCount; i++) {
            this.doc.setPage(i);
            
            // Footer line
            this.doc.setDrawColor(229, 231, 235);
            this.doc.line(this.margin, this.pageHeight - 20, this.pageWidth - this.margin, this.pageHeight - 20);
            
            // Footer text
            this.doc.setFontSize(9);
            this.doc.setFont('helvetica', 'normal');
            this.doc.setTextColor(107, 114, 128);
            this.doc.text('LegalGuard RegTech - Contract Analysis Report', this.margin, this.pageHeight - 12);
            this.doc.text(`Page ${i} of ${pageCount}`, this.pageWidth - this.margin, this.pageHeight - 12, { align: 'right' });
        }
    }

    public generateReport(
        result: AnalysisResult, 
        riskScore?: ComplianceRiskScore | null,
        filename?: string
    ): void {
        // Reset position
        this.currentY = this.margin;
        
        // Add sections
        this.addHeader();
        this.addSummarySection(result);
        
        if (riskScore) {
            this.addRiskScoreSection(riskScore);
        }
        
        this.addFlaggedClausesSection(result.flagged_clauses);
        this.addComplianceIssuesSection(result.compliance_issues);
        
        // Add footer to all pages
        this.addFooter();
        
        // Generate filename
        const defaultFilename = `LegalGuard-Analysis-${this.getJurisdictionName(result.jurisdiction)}-${new Date().toISOString().split('T')[0]}.pdf`;
        
        // Download the PDF
        this.doc.save(filename || defaultFilename);
    }
}

export const downloadAnalysisReport = (
    result: AnalysisResult, 
    riskScore?: ComplianceRiskScore | null,
    filename?: string
): void => {
    const generator = new PDFReportGenerator();
    generator.generateReport(result, riskScore, filename);
};
