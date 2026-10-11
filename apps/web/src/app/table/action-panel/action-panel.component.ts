import { Component, input } from '@angular/core';
import { LegalAction } from '../table-view.model';
@Component({ selector: 'app-action-panel', templateUrl: './action-panel.component.html', styleUrl: './action-panel.component.scss' })
export class ActionPanelComponent { readonly notification = input.required<string>(); readonly actions = input.required<readonly LegalAction[]>(); }
