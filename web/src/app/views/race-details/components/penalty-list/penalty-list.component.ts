import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { Participant, StringTypeUtils } from "src/types";
import { NG_IF, ROTATE } from "src/app/shared/animations";

@Component({
  selector: 'penalty-list',
  templateUrl: './penalty-list.component.html',
  styleUrls: ['./penalty-list.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [...ROTATE, ...NG_IF],
})
export class PenaltyListComponent {
  @Input() participants!: Participant[];
  @Input() collapsed: boolean = false;

  readableReason = StringTypeUtils.reason
}
