import { Topbar } from "./Topbar";
import { NavigationTabs } from "./NavigationTabs";
import styles from "./Actionbar.module.scss";

export function Actionbar() {
  return (
    <div className={styles.actionbar}>
      <Topbar />
      <NavigationTabs />
    </div>
  );
}
