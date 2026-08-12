import type { Meta, StoryObj } from "@storybook/react";
import { Card } from "./Card";
import "../styles/tokens.css";

const meta: Meta<typeof Card> = {
  title: "Molecules/Card",
  component: Card,
};
export default meta;

type Story = StoryObj<typeof Card>;

export const Default: Story = { args: { title: "Account", children: "Signed in as Charun." } };
export const LongTitle: Story = {
  args: { title: "A title far longer than the design ever anticipated", children: "…" },
};
